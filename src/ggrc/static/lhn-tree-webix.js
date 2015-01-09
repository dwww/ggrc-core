/*!
    Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
    Created By: dandv@google.com
    Maintained By: dandv@google.com
*/


/* TODO
 * counts - /search?q&counts_only=true&extra_columns=Workflow_All%3DWorkflow%2CWorkflow_Active%3DWorkflow%2CWorkflow_Draft%3DWorkflow%2CWorkflow_Inactive%3DWorkflow&extra_params=Workflow%3Astatus%3DActive%3BWorkflow_Active%3Astatus%3DActive%3BWorkflow_Inactive%3Astatus%3DInactive%3BWorkflow_Draft%3Astatus%3DDraft
     then match the results to the tree titles via Singular

    jQuery.ajax({
    url: 'search',
    data: {
        q: '',
        types: 'Program,Workflow_All,Audit,Regulation,Policy,Standard,Contract,Clause,Section,Objective,Control,Person,OrgGroup,Vendor,System,Process,DataAsset,Product,Project,Facility,Market',
        counts_only: true,
        extra_columns: 'Workflow_All=Workflow,Workflow_Active=Workflow,Workflow_Draft=Workflow,Workflow_Inactive=Workflow',
        extra_params: 'Workflow:status=Active;Workflow_Active:status=Active;Workflow_Inactive:status=Inactive;Workflow_Draft:status=Draft'
    }

    Add them as a field to the tree and set the node template


 * my vs. all objects
 * server-side filter via Search
 * tree doesn't resize, nix the can.js resizer and replace with http://webix.com/snippet/87509036 or http://webix.com/snippet/3738411f

 */


var objectTypes = [
    'audits',
    'controls' /* ignore program_controls, it's some metadata */,
    'objectives' /* ignore object_objectives */,
    'risk_assessments',
    'task_groups' /* ignore task_group_objects for now */,

    // these ones we moved to the root level above
    'regulations',
    'contracts',
    'policies',
    'standards'
];

/**
 * Get/reify an object from the server.
 * @param type - e.g. 'programs' or 'risk_assessments'. Must be an API plural name.
 * @param id - database ID of the object
 * @param [fields] - Limits the fields retrieved from the objects to those in this comma-separated list
 * @returns {*} Promise. Use it as getObject('programs', '2935').then(function (data) { ... });
 */
function getObject(type, id, fields) {
    return webix.ajax().header({
        'Accept': 'application/json'
    }).get('/api/' + type + '/' + id, {
        // __fields: 'name,description,etc.'
    })
}

/**
 * Gets the objects of a given type that are related ("mapped") to the given object.
 * @param object - the object for which we want to get the mapped objects. Must have a key for <type>
 * @param type - e.g. 'programs' or 'risk_assessments'. Must be an API plural name.
 * @param [fields] - Limits the fields retrieved from the objects to those in this comma-separated list. E.g. 'id,title,private' for the LHN tree.
 * @returns {*} Promise. Use it as getRelatedObjects(object, type, fields).then(function (data) { ... });
 */
function getRelatedObjects(object, type, fields) {
    if (type in object && object[type].length) {
        var relatedIds = object[type].map(function (object) { return object.id; });

        var parameters = {
            id__in: relatedIds
        };
        if (fields) parameters.__fields = fields;

        return webix.ajax().header({
            'Accept': 'application/json'
        }).get('/api/' + type, parameters);
    }
    // TODO return an empty promise instead
    return [];
}

// load templates
var objectDetailTemplate = webix.ajax().sync().get('/static/object-detail.html').responseText;

var tree = {
    id: 'lhn-tree',
    view: 'tree',
    position: 'flex',  // doesn't work - http://forum.webix.com/discussion/3641/bug-with-position-flex-doesn-t-resize-when-markup-container-size-changes
    template:"{common.icon()} {common.folder()} #title#",  // we might need to use a template function to show either the Title (for most objects), or the Name (for people) - http://docs.webix.com/desktop__html_templates.html#templatetypes

    // filterMode: {showSubItems: false },

    type: {
        icon: function getIconType(obj, common) {
            if (obj.open && obj.$count <= 0)
                return '<div class="webix_tree_custom fa-spinner fa-spin"></div>';

            return '<div class="webix_tree_'+(obj.$count ? (obj.open?"open":"close") : "none")+'"></div>';
        }
    },

    select: true,
    drag: true,
    // editable: http://docs.webix.com/datatree__editing.html#comment-1759430743
    editor: 'text',
    editValue: 'value',

    data: lhn_data,
    on: {
        onDataRequest: loadTreeChildren,
        onAfterSelect: function (nodeId) {
            // get the object and create its tabs
            var tree = this;
            var node = tree.getItem(nodeId);
            if (node.webix_kids || !node.$parent) return;
            var parent = tree.getItem(node.$parent);
            var apiPlural = typePlural2ApiPlural(parent.title);
            getObject(apiPlural, node.id).then(setTabs).fail(function (err){
                webix.message('Could not retrieve ' + apiPlural + ' ' + node.id);
            });
        },
        onBeforeSelect: function (nodeId) {
            var objectTabs = $$('object-tabs');
            objectTabs && objectTabs.destructor();
            /*tabIds.forEach(function (id) {
                $$('object-tabs').removeView(id);
            });*/
        }
    }
};

var treeTableColumns = [
    {
        id: 'title',
        header: 'Name',
        width: 400,
        adjust: true,
        template:"{common.treetable()} #title#"
    },
    {
        id: 'description', header: 'Description',
        adjust: true
    },
    {
        id: 'slug', header: 'Code',
        adjust: true
    },
    {
        id: 'status', header: 'State',
        adjust: true
    },
    {
        id: 'updated_at', header: 'Last update',
        adjust: true
    },
    { id: '', header: '', fillspace: 1,
        template: '<span style="float: right"><i class="fa fa-calendar"></i> <input type=checkbox></span>',
        css:"padding_less",
        width:100
    }
];

/**
 * Load the children of an LHN tree via the REST API
 * @param nodeId
 */
function loadTreeChildren(nodeId) {
    /* TODO paging: http://docs.webix.com/desktop__scroll_control.html#scrollinganddynamicloading
       http://docs.webix.com/desktop__paging.html
       http://docs.webix.com/samples/25_pager/02_apionly.html
       http://docs.webix.com/api__refs__ui.pager.html
    */
    var tree = this;
    var node = tree.getItem(nodeId);
    // if we wanted to show a big progress indicator - http://forum.webix.com/discussion/comment/3604/#Comment_3604
    node.$count = 0;  // webix workaround that will be fixed in 2.2 - http://forum.webix.com/discussion/comment/3590/#Comment_3590

    var apiPlural = typePlural2ApiPlural(node.title),
        typeSingular = cms_singularize(node.title);  // not lowercase

    // Use the search API because we have server-side filtering
    webix.ajax().get('search', {
        q: $$('tree-filter').getValue(),
        types: typeSingular  // the 's' in types refers to multiple type-s
    }).then(function (data) {
        var children = data.json().results.entries;
        webix.message('Loading ' + children.length + ' ' + apiPlural + '...');
        console.time('loadChildren.' + apiPlural);

        var childrenIds = children.map(function (child) {
            return child.id;
        });
        return webix.ajax().header({
            'Accept': 'application/json'
        }).get('/api/' + apiPlural, {
            id__in: childrenIds.slice(0, 300).join(','),  // the request for all ids may be too big; 459 sections was too big, 254 worked. IDs were 40digit.
            __fields: 'id,title,name,private'  // name is only for people
        });
    }).then(function (data) {
        // yes, the API is verbose like that: sections_collection.sections, as if 'sections' alone wasn't OK
        var children = data.json()[apiPlural + '_collection'][apiPlural];
        // process the children and prepare the data for display in the LHN tree
        children.forEach(function (child) {
            child.webix_kids = false;
            if (child.private) child.$css = 'private';
            if (apiPlural === 'people') child.title = child.name;
        });
        tree.parse({parent: nodeId, data: children});
        console.timeEnd('loadChildren.' + apiPlural);
        return false;
    })
}

/**
 * Set the tabs for "mapped" objects according to data in the object selected in the LHN
 * @param data
 */
function setTabs(data) {
    data = data.json();
    var type = Object.keys(data)[0];  // all object properties are under a key of the object type, e.g. 'program'
    var object = normalizeObject(data[type]);

    var tabs = new webix.ui({
        container: 'object-detail-container',
        position: 'flex',
        view: 'tabview',
        id: 'object-tabs',
        tabbar: {
            tabMinWidth: 180,
            optionWidth: 200,
            close: true
        },
        animate: true,
        cells: [
            {
                header: '<span class="webix_icon fa-info"></span> Info',
                body: {
                    // view: 'list',
                    id: 'object-info',
                    position: 'flex',
                    template: 'Information about this #type#: #title#',
                    data: object
                }
            }
        ]

    });

    //$$('object-info').parse(object);
    //$$('object-info').show();
    // TODO - force the active tab to show/render

    // get the related ("mapped") objects
    objectTypes.forEach(function (relatedType) {
        if (relatedType in object && object[relatedType].length) {
            var tabId = relatedType + '-tab';
            var relatedTypePlural = apiPlural2typePlural(relatedType);

            getRelatedObjects(object, relatedType).then(function (data) {

                var relatedObjects = normalizeObjects(data, relatedType);

                var treeTableId = relatedType + '-treetable';
                var objectDetailId = relatedType + '-details';

                $$('object-tabs').addView({
                    id: tabId,
                    header: '<span class="webix_icon ' + relatedType + '"></span> ' + relatedTypePlural + ' (' + object[relatedType].length + ')',
                    body: {
                        rows: [
                            {
                                cols: [
                                    {
                                        view: 'button',
                                        width: 200,
                                        value: 'Export to Excel', click: function () {
                                        $$(relatedType + '-treetable').exportToExcel();
                                    }
                                    },
                                    {
                                        view: 'button',
                                        width: 200,
                                        value: 'Export to PDF', click: function () {
                                        $$(relatedType + '-treetable').exportToPDF();
                                    }
                                    },
                                    {gravity: 2}
                                ]
                            },

                            {
                                id: relatedType + 'treetable-filter',
                                view: 'text',
                                label: 'Filter',
                                labelPosition: 'inline'
                            },
                            {
                                view: 'treetable',
                                id: treeTableId,
                                position: 'flex',

                                select: true,

                                autoheight: true,
                                resizeColumn: true,

                                columns: webix.copy(treeTableColumns),  // copy because the columns for each treetable are updated to reflect resizing

                                // yes, the API is verbose like that: audits_collection.audits, as if 'audits' alone wasn't OK
                                data: relatedObjects,

                                on: {
                                    onAfterSelect: function (elementId) {
                                        // hide the detail view if nothing is selected
                                        if (elementId)
                                            $$(objectDetailId).show();
                                        else
                                            $$(objectDetailId).hide();
                                    },

                                    // load objects linked ("mapped") to the current one under it
                                    onDataRequest: function (elementId) {
                                        var treetable = this;
                                        var node = treetable.getItem(elementId);
                                        node.$count = 0;  // Webix workaround until 2.2 TODO rm
                                        var object = normalizeObject(treetable.getItem(elementId));
                                        objectTypes.forEach(function (type) {
                                            if (type in object && object[type].length)
                                                getRelatedObjects(object, type).then(function (relatedObjects) {
                                                    relatedObjects = normalizeObjects(relatedObjects, type);
                                                    treetable.parse({parent: elementId, data: relatedObjects})
                                                })
                                        });
                                        return false;
                                    }

                                }

                            },
                            { view: 'resizer' },
                            {
                                id: objectDetailId,
                                hidden: true,  // will be shown only onAfterSelect from the treetable
                                // TODO: return an HTML template, http://docs.webix.com/api__ui.template_sethtml.html
                                // TODO big performance penalty; replace with objectDetailTemplate once forum.webix.com/discussion/comment/3667#Comment_3667 is solved
                                template: 'http->/static/object-detail.html',
                                autoheight: true,
                                on: {
                                    onBindRequest: function () {
                                        // http://forum.webix.com/discussion/3663/how-to-not-display-undefined-in-bound-templates-before-any-selection-is-made
                                        // if (Object.keys(this.data).length === 0)  // weirdly, this is NOT an object? TODO SO
                                            // this.setContent("Sorry, there is no data");
                                    }
                                }
                            }
                        ]
                    }
                });

                // enable filtering in the treetable
                $$(relatedType + 'treetable-filter').attachEvent('onTimedKeyPress', function () {
                    $$(treeTableId).filter("#title#", this.getValue());
                });

                // automatically show details for the currently selected object trom the treetable
                $$(objectDetailId).bind(treeTableId);


            });

        }

    });

}



webix.ready(function () {

    // TODO: nix the lhn-controller resizer. It's atrocious. As an exercise, try to change the size to anything but 240px in lhn-controller.js
    // https://github.com/reciprocity/ggrc-core/pull/2116/files#diff-1
    // By comparison, HTML layouts in Webix are embarrassingly simple - http://webix.com/blog/html-layouts-with-webix/
    // Or with JS, amazingly configurable: http://webix.com/snippet/0aa0a2cc
    webix.ui({
        container: 'lhn-tree-container',
        position: 'flex',
        rows: [
            {
                id: 'tree-filter',
                view: 'text',
                label: 'Search',
                labelPosition: 'inline'
            },
            tree
        ]
    });
    
    $$('tree-filter').attachEvent('onTimedKeyPress', function () {
        $$('lhn-tree').filter("#title#", this.getValue());
    });
    
});
