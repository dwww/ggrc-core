
/*!
    Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
    Created By: sasmita
    Maintained By: sasmita
*/
//----------------------------------------------------------------------------------------------
//Advanced search controller  extended from MultitypeObjectModalSelector
//
//----------------------------------------------------------------------------------------------



(function(can, $) {
  GGRC.Controllers.MultitypeObjectModalSelector("GGRC.Controllers.AdvancedSearchSelector", {
    defaults: {
          option_type_menu: null
        , option_descriptors: null
        , base_modal_view: "/static/mustache/search/advanced_search_base_modal.mustache"
        , option_items_view: "/static/mustache/search/advanced_search_option_items.mustache"
        , option_column_view: "/static/mustache/search/advanced_search_option_column.mustache"
        , option_type: null
        , option_model: null
        , object_model: null
        , join_model: null
    }
  }, {

  init_menu: function() {
      var menu, all_models = [],
          lookup = {
            governance: 0
          , business: 1
          , entities: 2
          };

      if (!this.options.option_type_menu) {
        menu = [
            { category: "Governance"
            , items: []
            }
          , { category: "Assets/Business"
            , items: []
            }
          , { category: "People/Groups"
            , items: []
            }
          ];

        //Add All Objects at the top of the list
        menu[0].items.push({
          model_name:"AllObjects",
          model_display:"All Objects"
        });

        can.each(this.options.option_descriptors, function(descriptor) {
          if ( descriptor.model.category === undefined ) {
            ;//do nothing
          }
          else {
            menu[lookup[descriptor.model.category] || 0].items.push({
                model_name: descriptor.model.shortName
              , model_display: descriptor.model.title_plural
            });
            //Save the model names for All Object search
            all_models.push(descriptor.model.shortName);
          }
        })

        this.options.option_type_menu = menu;
      }
      this.options.all_models = all_models;
      //hard code some of the submenu
      this.options.option_type_menu_2 = can.map([
            "Program","Regulation", "Policy", "Standard", "Contract", "Clause", "Section", "Objective", "Control",
            "Person", "System", "Process", "DataAsset", "Product", "Project", "Facility" , "Market"
            ],
            function(key) {
              return CMS.Models[key];
            }
      );
  }

  , set_option_descriptor: function(option_type) {
      //Set option descriptor for all objects
      if(option_type === "AllObjects") {
        var all_descriptor = {
          column_view : "/static/mustache/search/advanced_search_option_column.mustache",
          detail_view: "/static/mustache/selectors/multitype_option_detail.mustache",
          related_table_plural: "AllObjects",
          related_table_singular: "AllObject",
          related_model_singular: "AllObject",
          new_object_title: "AllObject",
          items_view: "/static/mustache/search/advanced_search_option_items.mustache",
          model: "AllObject"
        };
        this.options.option_descriptors["AllObjects"] = all_descriptor;
      }
      var self = this
        , descriptor = this.options.option_descriptors[option_type]
        ;

      if (option_type == null || option_type == "undefined")
        return;

      this.constructor.last_selected_options_type = option_type;

      can.Model.startBatch();

      this.context.attr('selected_option_type', option_type);
      this.context.attr('option_column_view', descriptor.column_view);
      this.context.attr('option_detail_view', descriptor.detail_view);
      this.context.attr('option_descriptor', descriptor);
      this.context.selected_options = [];
      this.context.attr('selected_result', can.compute(function() {
        return self.get_result_for_option(self.context.attr('selected_options'));
      }));
      this.context.attr('related_table_plural', descriptor.related_table_plural);
      this.context.attr('related_table_singular', descriptor.related_table_singular);
      this.context.attr('related_model_singular', descriptor.related_model_singular);
      this.context.attr('new_object_title', descriptor.new_object_title);
      this.options.option_items_view = descriptor.items_view;
      this.options.option_model = descriptor.model;
      if (!this.options.option_search_term)
        this.options.option_search_term = '';

      can.Model.stopBatch();
      //Refresh_option_list is done from the search button
      //this.refresh_option_list();
  }


  , refresh_option_list: function() {
        var self = this
          , current_option_model = this.options.option_model
          , current_option_model_name = current_option_model.shortName
          , current_search_term = this.options.option_search_term
          , active_fn
          , draw_fn
          , ctx = this.context
          ;

        active_fn = function() {
          return self.element &&
                 self.options.option_model === current_option_model &&
                 self.options.option_search_term === current_search_term;
        };

        draw_fn = function(options) {
          self.insert_options(options);
        };

        self.option_list.replace([]);
        self.element.find('.option_column ul.new-tree').empty();

        var join_model = GGRC.Mappings.join_model_name_for(
              this.options.object_model, current_option_model_name);
        var permission_parms = { __permission_type: 'read' };
        if (current_option_model_name == 'Program') {
          permission_parms = {
            __permission_type: 'create'
            , __permission_model: join_model
          };
        }

        if (ctx.owner){
          permission_parms.contact_id = ctx.owner.id;
        }

        if (current_option_model === "AllObject"){
          var models = this.options.all_models;
          return GGRC.Models.Search.search_for_types(current_search_term || '', models, permission_parms)
            .then(function (search_result){
              var options = [], op1, temp ; 
              if (active_fn()) {
                for(var i = 0; i < models.length; i++){
                  op1 = search_result.getResultsForType(models[i]);
                  temp = options.concat(op1);
                  options = temp;
                }

                self.option_list.replace([]);
                self.option_list.push.apply(self.option_list, options);
                self._start_pager(options, 20, active_fn, draw_fn);
                $('.advancedSearchButton').removeAttr('disabled');
              }
            });
        }

        return GGRC.Models.Search
          .search_for_types(
              current_search_term || '',
              [current_option_model_name],
              permission_parms)
          .then(function(search_result) {
            var options = [];

            if (active_fn()) {
              options = search_result.getResultsForType(current_option_model_name);

              self.option_list.replace([]);
              self.option_list.push.apply(self.option_list, options);
              self._start_pager(options, 20, active_fn, draw_fn);
              $('.advancedSearchButton').removeAttr('disabled');
            }
          });
    }

    //Search button click
    , ".advancedSearchButton:not([disabled]) click": "triggerSearch"

    , "#search keyup": function(el, ev) {
        if (ev.which == 13) {
          this.context.attr("option_search_term", el.val());
          this.triggerSearch();
        }
      }

    , "input[null-if-empty] change" : function(el, ev) {
      if(el.val() === "") {
        this.context.attr(el.attr("name"), null);
      }
    }

    , triggerSearch: function(){
      $('.advancedSearchButton').attr('disabled','disabled');
      
      // Remove Search Criteria text
      $('.results-wrap span.info').hide();
      var ctx = this.context;

      //Get the selected object value
      var selected = $("select.option-type-selector").val(),
        self = this,
        loader,
        term = ctx.option_search_term || "",
        filters = [],
        cancel_filter;

      this.set_option_descriptor(selected);

      ctx.filter_list.each(function(filter_obj) {
        if(cancel_filter || !filter_obj.search_filter) {
          cancel_filter = true;
          return;
        }
        //All Object
        if(selected === "AllObjects") {//create a multi filter
          var loaders , local_loaders = [], multi_loader;
          //Create a multi-list loader
          loaders = GGRC.Mappings.get_mappings_for(filter_obj.search_filter.constructor.shortName);
          can.each(loaders, function(loader, name) {
            if (loader instanceof GGRC.ListLoaders.DirectListLoader
                || loader instanceof GGRC.ListLoaders.ProxyListLoader) {
              local_loaders.push(name);
            }
          });

          multi_loader = new GGRC.ListLoaders.MultiListLoader(local_loaders).attach(filter_obj.search_filter);
          filters.push(multi_loader);
        }
        else {
          filters.push(
            // Must type filter here because the canonical mapping
            //  may be polymorphic.
            new GGRC.ListLoaders.TypeFilteredListLoader(
              GGRC.Mappings.get_canonical_mapping_name(filter_obj.search_filter.constructor.shortName, selected),
              [selected]
            ).attach(filter_obj.search_filter)
          );
        }
      });
      if(cancel_filter) {
        //missing search term.
        return;
      }

      if (filters.length > 0) {
        // For All Objects, make sure to load only those objects in the list of all_models
        // Multilist loader might load objects like g-drive folder and context
        // The Search list loader will filter those objects
        if(selected === "AllObjects") {
            filters.push(new GGRC.ListLoaders.SearchListLoader(function(binding) {
              return GGRC.Models.Search.search_for_types(
                term,
                self.options.all_models,
                { contact_id: binding.instance && binding.instance.id }
                ).then(function(mappings) {
                  return mappings.entries;
                });
            }).attach(ctx.owner || {}));
        }
        else if(ctx.owner || term){
          filters.push(new GGRC.ListLoaders.SearchListLoader(function(binding) {
              return GGRC.Models.Search.search_for_types(
                term,
                [selected],
                { contact_id: binding.instance && binding.instance.id }
                ).then(function(mappings) {
                  return mappings.entries;
                });
            }).attach(ctx.owner || {}));
        }
        
        //Object selected count and Add selected button should reset.
        //User need to make their selection again
        this.reset_selection_count();

        if (filters.length === 1) {
          loader = filters[0];
        } else {
          loader = new GGRC.ListLoaders.IntersectingListLoader(filters).attach();
        }

        this.last_loader = loader;
        self.option_list.replace([]);
        self.element.find('.option_column ul.new-tree').empty();
        loader.refresh_stubs().then(function(options) {
          var active_fn = function() {
            return self.element && self.last_loader === loader;
          };

          var draw_fn = function(options) {
            self.insert_options(options);
          };
          self.option_list.push.apply(self.option_list, options);
          $('.advancedSearchButton').removeAttr('disabled');
          self._start_pager(can.map(options, function(op) {
              return op.instance;
            }), 20, active_fn, draw_fn);
        });
      } //if (filters.length > 0)
      else {
        //Object selected count and Add selected button should reset.
        //User need to make their selection again
        this.reset_selection_count();

        // With no mappings specified, just do a general search
        //  on the type selected.
        this.last_loader = null;
        this.options.option_search_term = term;
        this.refresh_option_list();
        this.constructor.last_option_search_term = term;
      }
    }

    , autocomplete_select : function(el, ev, ui) {
      setTimeout(function(){
        el.val(ui.item.name || ui.item.email || ui.item.title, ui.item);
        el.trigger('change');
      }, 0);
      this.context.attr(el.attr("name"), ui.item);
    }

  });

  search_descriptor_view_option = {
    "Person": {
        column_view : GGRC.mustache_path + "/search/advanced_search_option_column.mustache",
        items_view  : GGRC.mustache_path + "/search/advanced_search_people_items.mustache"
    }
  };

  function get_search_multitype_option_set(data, column_view, item_view) {

    var join_descriptors = null,
        object_model_name = data.join_object_type,
        option_model_name = data.join_option_type,
        option_descriptors = {},
        option_set = {
            object_model: object_model_name
        },
        exclude_option_types = data.exclude_option_types ? data.exclude_option_types.split(",") : []
      ;

    if (!option_model_name) {
      join_descriptors =
        GGRC.Mappings.get_canonical_mappings_for(object_model_name);
    } else {
      join_descriptors = {};
      join_descriptors[option_model_name] = GGRC.Mappings.get_canonical_mapping(object_model_name, option_model_name);
    }

    can.each(join_descriptors, function(descriptor, far_model_name) {
      var option_model_name = descriptor.option_model_name || far_model_name;
      var extra_options = search_descriptor_view_option[option_model_name];


      //  If we have duplicate options, we want to use the first, so return
      //    early.
      //  Also return now if the descriptor is explicitly excluded from the
      //    set of descriptors for this modal.
      if (option_descriptors[option_model_name]
          || ~can.inArray(option_model_name, exclude_option_types)
          //  For some recently-added join settings, there is no join model, so
          //  short-circuit
          || !descriptor.model_name
          || !(descriptor instanceof GGRC.ListLoaders.ProxyListLoader))
        return;


      if (!option_set.default_option_descriptor)
        option_set.default_option_descriptor = "Program";

      if (!extra_options){
        extra_options = {
            column_view : column_view
          , items_view  : item_view
        }
      }

      option_descriptors[option_model_name] =
        ModalOptionDescriptor.from_join_model(
            descriptor.model_name
          , descriptor.option_attr
          , option_model_name
          , extra_options);

    });

    option_set.option_descriptors = option_descriptors;
    return option_set;
  }


  $(function() {
    $('body').on('click', '[data-toggle="multitype-search-modal-selector"]', function(e) {
      var $this = $(this)
        , options
        , data_set = can.extend({}, $this.data())
        ;

      can.each($this.data(), function(v, k) {
        data_set[k.replace(/[A-Z]/g, function(s) { return "_" + s.toLowerCase(); })] = v; //this is just a mapping of keys to underscored keys
        if(!/[A-Z]/.test(k)) //if we haven't changed the key at all, don't delete the original
          delete data_set[k];
      });

      //set up the options for new multitype Object  modal
      var column_view = GGRC.mustache_path + "/search/advanced_search_option_column.mustache",
      item_view =  GGRC.mustache_path + "/search/advanced_search_option_items.mustache" ;

      options = get_search_multitype_option_set(data_set, column_view, item_view);

      e.preventDefault();

      GGRC.Controllers.AdvancedSearchSelector.launch($this, options);
    });
  });

})(window.can, window.can.$);
