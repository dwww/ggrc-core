/*!
    Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
    Created By: dandv@google.com
    Maintained By: dandv@google.com
*/

/**

@author Dan Dascalescu, [@dandv](http://dandascalescu.com)
@overview # GGRC front-end built with [Webix](http://webix.com)

Webix was chosen as the UI components framework for GGRC after
[extensive research](http://stackoverflow.com/questions/200284/what-are-alternatives-to-extjs/2144878#2144878).

Runners-up include Dojo, lacking a modern theme (but @dandv started a [thread to get a Material Design
theme](http://dojo-toolkit.33424.n3.nabble.com/Material-Design-inspired-theme-td4004856.html) done),
and ExtJS, with a high learning curve.

 */

/* TODO
 * counts - /search?q&counts_only=true&extra_columns=Workflow_All%3DWorkflow%2CWorkflow_Active%3DWorkflow%2CWorkflow_Draft%3DWorkflow%2CWorkflow_Inactive%3DWorkflow&extra_params=Workflow%3Astatus%3DActive%3BWorkflow_Active%3Astatus%3DActive%3BWorkflow_Inactive%3Astatus%3DInactive%3BWorkflow_Draft%3Astatus%3DDraft
     then match the results to the tree titles via Singular

    webix.ajax({
    url: 'search',
    data: {
        q: '',
        types: 'Program,Workflow_All,Audit,Regulation,Policy,Standard,Contract,Clause,Section,Objective,Control,Person,OrgGroup,Vendor,System,Process,DataAsset,Product,Project,Facility,Market',
        counts_only: true,
        extra_columns: 'Workflow_All=Workflow,Workflow_Active=Workflow,Workflow_Draft=Workflow,Workflow_Inactive=Workflow',
        extra_params: 'Workflow:status=Active;Workflow_Active:status=Active;Workflow_Inactive:status=Inactive;Workflow_Draft:status=Draft'
    }

    Add them as a field to the tree and set the node template


 * LHN Workflow types + counts
 * resizable Details
 * working export
 * relevant mappings
 * real owners
 * my vs. all objects
 * "private" icon
 * server-side filter via Search
 * make RESTAPI return normalized objects already
 * tree doesn't resize, nix the can.js resizer and replace with http://webix.com/snippet/87509036 or http://webix.com/snippet/3738411f
 * save data with http://docs.webix.com/api__link__ui.datatable_ondataupdate_event.html

 */

/**
 * @var objectTypes
 */
var objectTypes = [
    // these types are direct keys of an object, e.g. var audits = getObject('programs', 123).audits;
    'audits',
    'controls' /* ignore program_controls, it's some metadata */,
    'objectives' /* ignore object_objectives */,
    'risk_assessments',
    'task_groups' /* ignore task_group_objects for now */,

    // these types were moved to root from under .directives by normalizeObject(object)
    'regulations',
    'contracts',
    'policies',
    'standards',
    'programs',

    // related_destinations, moved to root by normalizeObject(object)
    'data_assets',
    'facilities',
    'markets',
    'org_groups',
    'processes',
    'products',
    'projects',
    'systems',
    'vendors'
];

// load templates
// XXX With Webix < 2.2, HTML must NOT contain comments - http://forum.webix.com/discussion/comment/3667#Comment_3667
var objectDetailTemplate = webix.ajax().sync().get('/static/object-detail.html').responseText;



/**
 * Define the Webix properties of the LHN tree
 * @var
 * @type {{id: string, view: string, position: string, template: string, type: {icon: Function}, select: boolean, drag: boolean, data: (lhn_data|*), on: {onDataRequest: loadTreeChildren, onAfterSelect: Function, onBeforeSelect: Function}}}
 */
var tree = {
    id: 'lhn-tree',
    view: 'tree',
    position: 'flex',  // doesn't work - http://forum.webix.com/discussion/3641/bug-with-position-flex-doesn-t-resize-when-markup-container-size-changes
    template: '{common.icon()} {common.folder()} #title#',  // we might need to use a template function to show either the Title (for most objects), or the Name (for people) - http://docs.webix.com/desktop__html_templates.html#templatetypes

    // filterMode: {showSubItems: false },

    type: {
        // the expand/collapse icon, by default +/-
        icon: function getIconType(obj, common) {
            // if we're loading the children
            if (obj.open && obj.$count <= 0)
                return '<div class="webix_tree_custom fa-spinner fa-spin"></div>';
            // if the children have been loaded, display open/close or no expand/collapse icon if there are no children
            return '<div class="webix_tree_'+(obj.$count ? (obj.open? 'open' : 'close') : 'none')+'"></div>';
            // TODO might be able to simplify ^^ by NOT creating "webix_tree_programs" icons, but targeting .webix_tree .programs
        }
    },

    select: true,
    drag: true,
    // editable: http://docs.webix.com/datatree__editing.html#comment-1759430743
    // editor: 'text',
    // editValue: 'value',

    data: lhn_data,
    on: {
        onDataRequest: loadTreeChildren,
        onAfterSelect: function (nodeId) {
            // get the object and create its tabs
            var tree = this;
            var node = tree.getItem(nodeId);
            if (node.webix_kids || !node.$parent) return;  // do nothing for the grouping nodes like "Governance"
            var parent = tree.getItem(node.$parent);
            var apiPlural = RESTAPI.typePlural2ApiPlural(parent.title);
            RESTAPI.getObject(apiPlural, node.id).then(setTabs).fail(function (err){
                webix.message('Could not retrieve ' + apiPlural + ' ' + node.id);
            });
        },
        onBeforeSelect: function (nodeId) {
            var objectTabs = $$('object-tabs');
            objectTabs && objectTabs.destructor();  // TODO alternatively, remove all tabviews one by one: http://docs.webix.com/api__link__ui.tabview_removeview.html#comment-1784100647
        }
    }
};


/**
 * Define the [TreeTable columns](http://docs.webix.com/api__link__ui.treetable_columns_config.html)
 * @var
 */
var treeTableColumns = [
    {
        id: 'title',  // `id is the key in each object that supplies the value for this column
        header: 'Name',  // the name of the Webix treetable column
        sort: 'string',
        minWidth: 200,
        fillspace: true,
        adjust: true,
        template: '{common.treetable()} #title#',  // include the expand/collapse button and the icon
        // to include checkbox: template:"{common.space()}{common.icon()}{common.treecheckbox()}{common.folder()}#value#"; and add 'threeState: true,' to the treetable definition
        exportAsTree: true  // false -> export as flat column
        // TODO bug - missing column separator before the next column
    },
    {
        id: 'owner', header: 'Owner',
        sort: 'string',
        adjust: true
    },
    {
        id: 'slug', header: 'Code',
        // header: ['Code', {content: 'textFilter'}],
        sort: 'string',
        css: {'text-align' : 'right'},  // inline style
        adjust: true
    },
    {
        id: 'status',
        header: [  // two-row header
        //    'State',
            { content: 'selectFilter' }  // predefined column content type that builds a drop-down of the values in the column
        ],
        sort: 'string',
        adjust: true
    },
    {
        id: 'updated_at', header: 'Last update',
        sort: 'date',
        adjust: true
    },
    {
        id: 'buttons', header: '<span style="float: right"><i class="fa fa-eye"></i> <i class="fa fa-gear"></i></span>',
        template: '<span style="float: right"><i class="fa fa-calendar"></i> <input type=checkbox></span>',
        css: 'padding_less',  // CSS class
        width: 100
    }
];


/**
 * Returns a [TreeTable](http://docs.webix.com/api__refs__ui.datatable.html) configuration object for Webix
 * @param {string} id - desired id for the table
 * @param {object[]} data
 * @param {string} detailPaneId - the id of a slave view that shows details about the currently select
 * @returns {{view: string, id: *, position: string, type: {icon: Function}, select: string, multiselect: boolean, editable: boolean, autoheight: boolean, resizeColumn: boolean, columns: *, leftSplit: number, data: *, on: {onAfterSelect: Function, onAfterFilter: Function, onDataRequest: loadTreeTableChildren, onAfterLoad: Function}}}
 */
function treeTableConfig(id, data, detailPaneId) {
    return {
        view: 'treetable',
        id: id,
        position: 'flex',  // TODO test after Webix 2.2

        type: {
            // the expand/collapse icon, by default +/-
            icon: function getTreeTableIconType(obj, common) {
                // if we're loading the children
                if (obj.open && obj.$count === -1)
                    return '<div class="webix_tree_custom fa-spinner fa-spin"></div>';
                // if the children have been loaded, display open/close or no expand/collapse icon if there are no children
                return '<div class="webix_tree_'+(obj.$count ? (obj.open? 'open' : 'close') : 'none')+'"></div>';
            }
        },

        select: 'row',
        multiselect: true,

        editable: false,

        autoheight: true,
        resizeColumn: true,

        columns: webix.copy(treeTableColumns),  // copy because the columns for each treetable are updated to reflect resizing
        leftSplit: 1,  // freeze the first column

        // yes, the API is verbose like that: audits_collection.audits, as if 'audits' alone wasn't OK
        data: data,

        on: {
            onAfterSelect: function (data, preserved) {
                // show the detail view when a row is selected
                $$(detailPaneId).show();
            },
            onAfterFilter: function (data, preserved) {
                // hide the detail view after filtering, due to a Webix bug - http://forum.webix.com/discussion/comment/3693/#Comment_3693 TODO
                $$(detailPaneId).hide();
            },

            // load objects linked ("mapped") to the current one under it
            onDataRequest: loadTreeTableChildren,

            // adjust column widths after loading new data - http://forum.webix.com/discussion/comment/3582/#Comment_3582
            onAfterLoad: function () {
                var treetable = this;
                /*treetable.eachColumn(function (columnId) {
                    // TODO rm when fix for keep an eye on http://forum.webix.com/discussion/3694/treetable-datatable-adjustcolumn-only-adjusts-after-all-rows-have-been-loaded
                    if (!treetable.getColumnConfig(columnId).fillspace)
                        treetable.adjustColumn(columnId, 'all');  // don't ajust the last column because it has fillspace = 1
                });*/
                // treetable.adjustColumn('title', 'data'); - we have fillspace: true for the title
                // TODO sort by the current sort column
            }
        }
    }
}



/**
 * Load the children of an LHN tree via the REST API. Used as the onDataRequest by the tree.
 * @param {String} nodeId - The id of the node whole children should be loaded
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
    node.$count = 0;  // webix workaround to avoid loading twice. Will be fixed in 2.2 - http://forum.webix.com/discussion/comment/3590/#Comment_3590 TODO rm

    var apiPlural = RESTAPI.typePlural2ApiPlural(node.title),
        typeSingular = RESTAPI.typePlural2Singular(node.title);  // not lowercase

    // Use the search API because we have server-side filtering; can't use the /apiPlural endpoint
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
            __fields: 'id,title,name,private'  // 'name' is only for people; all other objects have 'title'
        });
    }).then(function (data) {
        // yes, the API is verbose like that: sections_collection.sections, as if 'sections' alone wasn't OK
        // TODO call normalize instead
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
 * Load objects linked ("mapped") to the current one under it. Used as onDataRequest by the treetable.
 * @param {String} elementId - The id of the node whose children should be loaded
 */
function loadTreeTableChildren(elementId) {
    var treetable = this;
    var object = treetable.getItem(elementId);
    RESTAPI.normalizeObject(object);  // TODO this should arrive here normalized
    // get all the parents of these objects, so we can remove them from relatedObjects because we don't want cycles in the tree
    var visitor = object, parents = {};
    do parents[visitor.id] = true; while (visitor = treetable.getItem(visitor.$parent));
    // check for related objects of any type: audits, controls, ..., vendors
    objectTypes.forEach(function (type) {
        RESTAPI.getRelatedObjects(object, type).then(function (data) {
            var relatedObjects = RESTAPI.normalizeObjects(data.json());
            var relatedChildren = [];  // grep/filter
            relatedObjects.forEach(function (child) {
                if (!parents[child.id])
                    relatedChildren.push(child);
            });
            if (relatedChildren.length)  // TODO Webix bug: http://forum.webix.com/discussion/3696/treetable-nodes-render-blank-ondatarequest
                treetable.parse({parent: elementId, data: relatedChildren});
            else console.log('Zero children left for', type);
            // TODO bug: for some objects the - stays - after expansion to no children; for others, it disappears. Check in dandv -> Controls -> area recon
        })
    });
    object.$count = 0;  // Webix workaround to avoid loading twice. Will be fixed in 2.2 - http://forum.webix.com/discussion/comment/3590/#Comment_3590
    // TODO apparently not necessary for treetable on localost but did this happen on AppEngine, so setting it as insurance
    return false;
}
/**
 * Set the tabs for "mapped" objects according to data in the object selected in the LHN
 * @param data
 */
function setTabs(data) {
    data = data.json();
    var type = Object.keys(data)[0];  // all object properties are under a key of the object type, e.g. 'program'
    var object = RESTAPI.normalizeObject(data[type]);

    var tabs = new webix.ui({
        container: 'object-detail-container',
        position: 'flex',
        rows: [
            {
                view: 'template', type: 'header', template: '#title#', data: object
            },
            {
                view: 'tabview',  // http://docs.webix.com/api__refs__ui.tabview.html
                id: 'object-tabs',
                tabbar: {
                    tabMinWidth: 180,
                    optionWidth: 200,
                    close: true
                },
                animate: true,
                cells: [
                    {
                        // header: '<span class="webix_icon fa-info"></span> Info',
                        header: '<span class="webix_icon info"></span> Info',
                        body: {
                            // view: 'list',
                            id: 'object-info',
                            position: 'flex',
                            template: 'Information about this #type#: #title#',
                            data: object
                        }
                    }
                ]
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

            RESTAPI.getRelatedObjects(object, relatedType).then(function gotRelatedObjects(data) {

                var relatedObjects = RESTAPI.normalizeObjects(data.json());

                var treeTableId = relatedType + '-treetable';
                var objectDetailId = relatedType + '-details';
                var relatedTypeUserFriendly = RESTAPI.apiPlural2typePlural(relatedType);

                // TODO: ensure consistent order by creating all the tabs but keeping them hidden, then showing when data arrives
                // TODO also don't destruct, but replace the contents... faster but more memory-leak prone?
                $$('object-tabs').addView({
                    id: tabId,
                    header: '<span class="webix_icon ' + relatedType + '"></span> ' + relatedTypeUserFriendly + ' (' + object[relatedType].length + ')',
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
                                    { gravity: 2 }  // sizing
                                ]
                            },

                            {
                                id: relatedType + 'treetable-filter',
                                view: 'text',
                                label: 'Filter',
                                labelPosition: 'inline'
                            },
                            treeTableConfig(treeTableId, relatedObjects, objectDetailId),
                            { view: 'resizer' },
                            {
                                id: objectDetailId,
                                hidden: true,  // will be shown only onAfterSelect from the treetable
                                template: objectDetailTemplate,
                                // autoheight: true,
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

                // establish initial sorting
                var treeTable = $$(treeTableId);
                treeTable.sort("#title#");
                treeTable.markSorting("title", "asc");

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
                view: 'search',
                placeholder: 'Filter my objects...'
            },
            tree
        ]
    });
    
    $$('tree-filter').attachEvent('onTimedKeyPress', function () {
        $$('lhn-tree').filter("#title#", this.getValue());
    });
    
});
