This file lists how to accomplish tasks with [Webix](http://webix.com).

# Main resources

* [Homepage](http://webix.com) - check the demos!
* [Demo of an app similar to GGRC](http://webix.com/demos/admin-app)
* [Documentation](http://docs.webix.com)
  * [Guides / tutorials](http://docs.webix.com/desktop__basic_tasks.html)
* [Tons of samples for each component](http://docs.webix.com/samples/)
* [Forum](http://forum.webix.com) and [dandv's questions](http://forum.webix.com/profile/discussions/9889/dandv)
* [Snippet playground](http://webix.com/snippet) - a JSFiddle/JSBin/Plunkr for Webix
* [GitHub](http://github.com/webix/tracker)

Below are selected resources from the pages listed above.

# [Styling](http://docs.webix.com/desktop__styling_and_animation.html)

* Styling Datatable - http://docs.webix.com/samples/15_datatable/21_styling/index.html

* Datatable CSS: http://docs.webix.com/desktop__datatable_css.html

* [Tree styling](http://docs.webix.com/samples/17_datatree/03_styles/index.html)

* Tree CSS: http://docs.webix.com/desktop__datatree_css.html

* Tabbar CSS: http://docs.webix.com/desktop__tabbar_css.html

* Material Design skin - http://docs.webix.com/samples/16_skins/index.html



# [Components](http://docs.webix.com/desktop__components.html)

* [Layouts, saving to the server](http://docs.webix.com/desktop__dynamic_layout.html)

* Context menu: http://docs.webix.com/samples/03_menu/04_context.html

* List advanced template: http://docs.webix.com/samples/05_list/17_advanced_template.html

* Templated tooltips: http://docs.webix.com/samples/06_dataview/02_templates/06_tooltip.html

* External HTML template: http://docs.webix.com/desktop__html_templates.html#templatetypes

* Progress indicators: http://docs.webix.com/samples/19_api/index.html

* Resizable tabbar properties: http://docs.webix.com/desktop__responsive_tabbar.html

* Reorder lists with drag handle: http://docs.webix.com/samples/22_dnd/03_drag_handle.html

* Tabs with icons and close button, added dynamically: http://webix.com/snippet/48c7c966

* Changing properties on the fly: http://docs.webix.com/api__link__ui.tree_customize.html or http://docs.webix.com/api__link__ui.tree_define.html

* Loading message: http://docs.webix.com/samples/15_datatable/01_loading/05_load_message.html

* Overlay message when there is no data: http://docs.webix.com/samples/15_datatable/01_loading/06_nodata_message.html

* Grid filtering: http://docs.webix.com/samples/15_datatable/03_filtering/index.html

* Custom checkbox and radio: http://docs.webix.com/samples/15_datatable/04_editing/08_custom_checkbox.html

* Validation: http://docs.webix.com/samples/15_datatable/25_validation/index.html

* Routes: http://docs.webix.com/samples/30_backbone/06_routes_webix.html

* Refined binding between list and form within larger app: http://webix.com/demos/user.html

* [Creating custom components](http://docs.webix.com/desktop__custom_component.html)

## Templates

* [Templates](http://docs.webix.com/desktop__html_templates.html) for every component. They only substitute #<key>#.

* Item [types](http://docs.webix.com/desktop__type.html) define display properties common across all items in a component.
  You can [include the result of arbitrary functions in each template](http://docs.webix.com/desktop__type.html).

## Datatable

* Datatable columns: http://docs.webix.com/api__link__ui.treetable_columns_config.html

* Datatable tooltips: http://docs.webix.com/samples/15_datatable/09_columns/08_tooltips.html

* [Datatable sizing](http://docs.webix.com/datatable__sizing.html) and [autosizing sample](http://docs.webix.com/samples/15_datatable/11_sizing/index.html)

* Datatable templates: http://docs.webix.com/samples/15_datatable/20_templates/index.html

* [Colummns configuration](http://docs.webix.com/datatable__columns_configuration.html) and how to attach a column with an external data source

* [Treetable filtering](http://docs.webix.com/samples/15_datatable/30_treetable/04_filter.html)


## Trees

* [Node templates](http://docs.webix.com/datatree__node_templates.html) in trees or treetables: common.icon()/folder()/checkbox()


# [Data loading](http://docs.webix.com/desktop__data_loading.html)

* [DataStore updated event](http://docs.webix.com/api__datastore_onstoreupdated_event.html) can be used to refresh components after the underlying data has changed

* Dynamic loading through data proxy: http://docs.webix.com/samples/15_datatable/16_dyn_loading/07_dyn_proxy.html

* Data binding: http://docs.webix.com/api__link__ui.template_bind.html

* [Server-side integration](http://docs.webix.com/desktop__serverside.html

* [mapping the JSON response fields](http://docs.webix.com/helpers__data_drivers.html#customizingdatadriver for )


# Composing components into new ones

```js
webix.protoUI({
    name: 'edittreetable'
}, webix.EditAbility, webix.ui.treetable);
```

```
webix.protoUI({
  name: 'progressTree'
}, webix.ProgressBar, webix.ui.tree);
```

# Basic form

```js
{
    view: 'form', id: relatedObjects + '-form', scroll: false,
    elements:[
        { view: 'text', name: 'title', label: 'Title' },
        { view: 'textarea', name: 'description', label: 'Description' },
        { view: 'button', value: 'Save', click: '$$("form1").save() }
    ]

}
```
