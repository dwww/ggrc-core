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
 * tree doesn't resize, nix the can.js resizer and replace with http://webix.com/snippet/87509036

 */



var tree = {
    id: 'lhn-tree',
    view: 'progressTree',
    position: 'flex',  // doesn't work - http://forum.webix.com/discussion/3641/bug-with-position-flex-doesn-t-resize-when-markup-container-size-changes
    template:"{common.icon()} {common.folder()} #title#",  // we might need to use a template function to show either the Title (for most objects), or the Name (for people) - http://docs.webix.com/desktop__html_templates.html#templatetypes

    // filterMode: {showSubItems: false },

    /*
    TODO set the icon type to spin while loading - see http://webix.com/snippet/ceb3ef4b
    type:{
        icon: function getIconType(obj, common) {
            if (obj.open && obj.$count <= 0)
                return '<div class="webix_tree_open fa-spinner fa-spin"></div>';

            return '<div class="webix_tree_' + (obj.open? '"open' : '"close') + '"></div>';
        }
    },*/

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
            webix.ajax().header({
                'Accept': 'application/json'
            }).get('/api/' + apiPlural + '/' + node.id, {
                // __fields: 'name,description,etc.'
            }).then(setTabs);
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
    tree.showProgress();
    node.$count = 0;  // webix workaround - http://forum.webix.com/discussion/comment/3590/#Comment_3590

    var apiPlural = typePlural2ApiPlural(node.title),
        typeSingular = cms_singularize(node.title);  // not lowercase

    // use promises for an easy to follow logical flow, without callbacks
    webix.ajax().get('search', {
        q: '',
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
 * Set the tabs according to data in the object
 * @param data
 */
function setTabs(data) {
    data = data.json();
    var type = Object.keys(data)[0];  // all object properties are under a key of the object type, e.g. 'program'
    var object = data[type];

    // move to the root lever the "directive"-type object (why are they under the "directive" key anyway?)
    object.directives && object.directives.forEach(function (directive) {
        // each has e.g. `href: "/api/policies/5938"`, `id: 5938`, `type: "Policy"`
        var plural = typeSingular2apiPlural(directive.type);
        plural in object? object[plural].push(directive) : object[plural] = [directive];
    });

    // TODO related_destinations

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

    [
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
    ].forEach(function (relatedObjects) {
        if (relatedObjects in object && object[relatedObjects].length) {
            var relatedIds = object[relatedObjects].map(function (object) { return object.id; });
            var relatedTypePlural = apiPlural2typePlural(relatedObjects);

            webix.ajax().header({
                'Accept': 'application/json'
            }).get('/api/' + relatedObjects, {
                id__in: relatedIds
                // __fields: 'name,description,etc.'
            }).then(function (data) {
                var tabId = relatedObjects + '-tabs';
                tabIds.push(tabId);

                $$('object-tabs').addView({
                    id: tabId,
                    header: '<span class="webix_icon ' + relatedObjects + '"></span> ' + relatedTypePlural + ' (' + object[relatedObjects].length + ')',
                    body: {
                        rows: [
                            {
                                cols: [
                                    {
                                        view: 'button',
                                        width: 200,
                                        value: 'Export to Excel', click: function () {
                                        $$(relatedObjects + '-treetable').exportToExcel();
                                    }
                                    },
                                    {
                                        view: 'button',
                                        width: 200,
                                        value: 'Export to PDF', click: function () {
                                        $$(relatedObjects + '-treetable').exportToPDF();
                                    }
                                    },
                                    {gravity: 2}
                                ]
                            },

                            {
                                id: relatedObjects + 'treetable-filter',
                                view: 'text',
                                label: 'Filter',
                                labelPosition: 'inline'
                            },
                            {
                                view: 'treetable',
                                id: relatedObjects + '-treetable',
                                position: 'flex',

                                select: true,

                                autoheight: true,
                                resizeColumn: true,

                                columns: [
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
                                ],

                                // yes, the API is verbose like that: audits_collection.audits, as if 'audits' alone wasn't OK
                                data: data.json()[relatedObjects + '_collection'][relatedObjects]

                            },
                            {   view:"resizer"  },
                            {
                                cols: [
                                    {
                                        template: "<h2>Details</h2>#description#<p>Start date: #start_date#<p>End date: #end_date#",
                                        id: relatedObjects + '-details',
                                        height: 300,
                                        on: {
                                            onBindRequest: function () {
                                                // http://forum.webix.com/discussion/3663/how-to-not-display-undefined-in-bound-templates-before-any-selection-is-made
                                                // if (Object.keys(this.data).length === 0)  // weirdly, this is NOT an object? TODO SO
                                                    // this.setContent("Sorry, there is no data");
                                            }
                                        }
                                    },
                                    {
                                        view: 'form', id: relatedObjects + '-form', scroll:false,
                                        elements:[
                                            { view: 'text', name: 'title', label: 'Title' },
                                            { view: 'textarea', name: 'description', label: 'Description' },
                                            { view: 'button', value: 'Save' /*, click: '$$("form1").save()'*/ }
                                        ]

                                    }
                                ]

                            }
                        ]
                    }
                });

                $$(relatedObjects + 'treetable-filter').attachEvent('onTimedKeyPress', function () {
                    $$(relatedObjects + '-treetable').filter("#title#", this.getValue());
                });


                $$(relatedObjects + '-details').bind(relatedObjects + '-treetable', function (data) {
                    webix.message(data);
                });

                $$(relatedObjects + '-form').bind(relatedObjects + '-treetable', function (data) {
                    webix.message(data);
                });

            });

        }

    });


    /*people & object_people - excludes the task contact & modified_by - those are implicitly added to the People tab
    program_directives & directives: regulations, contracts, policies, standards
    related_destinations: systems, processes, data assets, products, projects, facilities, markets, org groups, vendors
    workflow tasks is synthetically computed*/
}



webix.protoUI({
  name: 'progressTree'
}, webix.ProgressBar, webix.ui.tree);

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
