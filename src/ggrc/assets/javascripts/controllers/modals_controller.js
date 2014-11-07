/*!
    Copyright (C) 2013 Google Inc., authors, and contributors <see AUTHORS file>
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
    Created By: brad@reciprocitylabs.com
    Maintained By: brad@reciprocitylabs.com
*/

(function(can, $) {

can.Control("GGRC.Controllers.Modals", {
  BUTTON_VIEW_DONE : GGRC.mustache_path + "/modals/done_buttons.mustache"
  , BUTTON_VIEW_CLOSE : GGRC.mustache_path + "/modals/close_buttons.mustache"
//  BUTTON_VIEW_SAVE
  , BUTTON_VIEW_SAVE_CANCEL : GGRC.mustache_path + "/modals/save_cancel_buttons.mustache"
  , BUTTON_VIEW_SAVE_CANCEL_DELETE : GGRC.mustache_path + "/modals/save_cancel_delete_buttons.mustache"

  , defaults : {
    preload_view : GGRC.mustache_path + "/dashboard/modal_preload.mustache"
    , content_view : GGRC.mustache_path + "/help/help_modal_content.mustache"
    , header_view : GGRC.mustache_path + "/modals/modal_header.mustache"
    , button_view : null
    , model : null    // model class to use when finding or creating new
    , instance : null // model instance to use instead of finding/creating (e.g. for update)
    , new_object_form : false
    , mapping : false
    , find_params : {}
    , add_more : false
    , ui_array : []
    , reset_visible : false
  }

  , init : function() {
    this.defaults.button_view = this.BUTTON_VIEW_DONE;
  }

  , confirm : function(options, success, dismiss) {
    var $target = $('<div class="modal hide"></div>');
    $target
    .modal({ backdrop: "static" })
    .ggrc_controllers_modals(can.extend({
      new_object_form : false
      , button_view : GGRC.mustache_path + "/modals/confirm_buttons.mustache"
      , modal_confirm : "Confirm"
      , modal_description : "description"
      , modal_title : "Confirm"
      , content_view : GGRC.mustache_path + "/modals/confirm.mustache"
    }, options))
    .on('click', 'a.btn[data-toggle=confirm]', function(e) {
      var params = $(e.target).closest('.modal').find('form').serializeArray();
      $target.modal('hide').remove();
      success && success(params, $(e.target).data('option'));
    })
    .on('click.modal-form.close', '[data-dismiss="modal"]', function() {
      $target.modal('hide').remove();
      dismiss && dismiss();
    });
  }
}, {
  init : function() {
    if (!(this.options instanceof can.Observe)) {
      this.options = new can.Observe(this.options);
    }

    if(!this.element.find(".modal-body").length) {
      can.view(this.options.preload_view, {}, this.proxy("after_preload"));
    } else {
      this.after_preload()
    }
    //this.options.attr("mapping", !!this.options.mapping);
  }

  , after_preload : function(content) {
    var that = this;
    if (content) {
      this.element.html(content);
    }
    this.options.attr("$header", this.element.find(".modal-header"));
    this.options.attr("$content", this.element.find(".modal-body"));
    this.options.attr("$footer", this.element.find(".modal-footer"));
    this.on();
    this.fetch_all()
      .then(this.proxy("apply_object_params"))
      .then(this.proxy("serialize_form"))
      .then(function() {
        // If the modal is closed early, the element no longer exists
        that.element && that.element.trigger('preload')
      })
      .then(this.proxy("autocomplete"));
  }

  , apply_object_params : function() {
    var self = this;

    if (this.options.object_params)
      this.options.object_params.each(function(value, key) {
        self.set_value({ name: key, value: value });
      });
  }

  , "input[data-lookup] focus" : function(el, ev) {
    this.autocomplete(el);
  }
  , "input[data-lookup] keyup" : function(el, ev) {
    // Set the transient field for validation
    var name = el.attr('name').split('.'),
        instance = this.options.instance,
        value = el.val();

    name.pop(); //set the owner to null, not the email
    instance._transient || instance.attr("_transient", new can.Observe({}));
    can.reduce(name.slice(0, -1), function(current, next) {
      current = current + "." + next;
      instance.attr(current) || instance.attr(current, new can.Observe({}));
      return current;
    }, "_transient");
    instance.attr(["_transient"].concat(name).join("."), value);
  }

  , autocomplete : function(el) {
    $.cms_autocomplete.call(this, el);
  }

  , autocomplete_select : function(el, event, ui) {
    var original_event,
        that = this;

    $('#extended-info').trigger('mouseleave'); // Make sure the extra info tooltip closes
      var path = el.attr("name").split(".")
        , instance = this.options.instance
        , index = 0
        , prop = path.pop();

      if (/^\d+$/.test(path[path.length - 1])) {
        index = parseInt(path.pop(), 10);
        path = path.join(".");
        if (!this.options.instance.attr(path)) {
          this.options.instance.attr(path, []);
        }
        this.options.instance.attr(path).splice(index, 1, ui.item.stub());
      }
      else {
        path = path.join(".");
        this.options.instance.attr(path, ui.item.stub());
        // Make sure person name/email gets written to the input field
        setTimeout(function(){
          el.val(ui.item.title || ui.item.name || ui.item.email);
          instance._transient || instance.attr("_transient", new can.Observe({}));
          can.reduce(path.split("."), function(current, next) {
            current = current + "." + next;
            instance.attr(current) || instance.attr(current, new can.Observe({}));
            return current;
          }, "_transient");
          instance.attr("_transient." + path, ui.item[prop]);
          el.blur();
        }, 50);
      }
  }

  , immediate_find_or_create : function(el, ev, data) {
    var that = this
    , prop = el.data("drop")
    , model = CMS.Models[el.data("lookup")]
    , params = { context : that.options.instance.context && that.options.instance.context.serialize ? that.options.instance.context.serialize() : that.options.instance.context };

    setTimeout(function() {
      params[prop] = el.val();
      el.prop("disabled", true);
      model.findAll(params).then(function(list) {
        if(list.length) {
          that.autocomplete_select(el, ev, { item : list[0] });
        } else {
          new model(params).save().then(function(d) {
            that.autocomplete_select(el, ev, { item : d });
          });
        }
      })
      .always(function() {
        el.prop("disabled", false);
      });
    }, 100);
  }
  , "input[data-lookup][data-drop] paste" : "immediate_find_or_create"
  , "input[data-lookup][data-drop] drop" : "immediate_find_or_create"



  , fetch_templates : function(dfd) {
    var that = this;
    dfd = dfd ? dfd.then(function() { return that.options; }) : $.when(this.options);
    return $.when(
      can.view(this.options.content_view, dfd)
      , can.view(this.options.header_view, dfd)
      , can.view(this.options.button_view, dfd)
    ).done(this.proxy('draw'));
  }

  , fetch_data : function(params) {
    var that = this;
    var dfd;
    params = params || this.find_params();
    params = params && params.serialize ? params.serialize() : params;
    if (this.options.skip_refresh && this.options.instance) {
      return new $.Deferred().resolve(this.options.instance);
    }
    else if (this.options.instance) {
      dfd = this.options.instance.refresh();
    }
    else if (this.options.model) {
      dfd = this.options.new_object_form
          ? $.when(this.options.attr("instance", new this.options.model(params).attr("_suppress_errors", true)))
          : this.options.model.findAll(params).then(function(data) {
            var h;
            if(data.length) {
              that.options.attr("instance", data[0]);
              return data[0].refresh(); //have to refresh (get ETag) to be editable.
            } else {
              that.options.attr("new_object_form", true);
              that.options.attr("instance", new that.options.model(params));
              return that.options.instance;
            }
          }).done(function() {
            // Check if modal was closed
            if(that.element !== null)
              that.on(); //listen to instance.
          });
    }
    else {
      this.options.attr("instance", new can.Observe(params));
      that.on();
      dfd = new $.Deferred().resolve(this.options.instance);
    }

    return dfd.done(function() {

      // If the modal is closed early, the element no longer exists
      if (that.element) {
        // This is to trigger `focus_first_element` in modal_ajax handling
        that.element.trigger("loaded");
      }


      that.options.instance._transient || that.options.instance.attr("_transient", new can.Observe({}));
      that.options.instance.form_preload && that.options.instance.form_preload(that.options.new_object_form);
    });
  }

  , fetch_all : function() {
    return this.fetch_templates(this.fetch_data(this.find_params()));
  }

  , find_params: function() {
    return this.options.find_params.serialize ? this.options.find_params.serialize() : this.options.find_params
  }

  , draw : function(content, header, footer) {
    // Don't draw if this has been destroyed previously
    if (!this.element) {
      return;
    }

    can.isArray(content) && (content = content[0]);
    can.isArray(header) && (header = header[0]);
    can.isArray(footer) && (footer = footer[0]);

    header != null && this.options.$header.find("h2").html(header);
    content != null && this.options.$content.html(content).removeAttr("style");
    footer != null && this.options.$footer.html(footer);

    this.setup_wysihtml5();

    //Update UI status array
    var $form = $(this.element).find('form');
    var tab_list = $form.find('[tabindex]');
    var hidable_tabs = 0;
    for (var i = 0; i < tab_list.length; i++) {
      if ($(tab_list[i]).attr('tabindex') > 0)
        hidable_tabs++;
    }
    //ui_array index is used as the tab_order, Add extra space for skipped numbers
    var storable_ui = hidable_tabs + 10;
    for(var i = 0; i < storable_ui; i++) {
      //When we start, all the ui elements are visible
      this.options.ui_array.push(0);
    }
  }

  , setup_wysihtml5 : function() {
    if (!this.element) {
      return;
    }
    this.element.find('.wysihtml5').each(function() {
      $(this).cms_wysihtml5();
    });
  }

  , "input:not(isolate-form input), textarea:not(isolate-form textarea), select:not(isolate-form select) change" : function(el, ev) {
      this.options.instance.removeAttr("_suppress_errors");
      // Set the value if it isn't a search field
      if(!el.hasClass("search-icon")
        || el.is("[null-if-empty]")
           && (!el.val() || el.val().length === 0)
      ) {
        this.set_value_from_element(el);
      }
  }

  , "input:not([data-lookup], isolate-form *), textarea keyup" : function(el, ev) {
      if (el.prop('value').length === 0 ||
        (typeof el.attr('value') !== 'undefined' && el.attr('value').length === 0)) {
        this.set_value_from_element(el);
      }
  }

  , serialize_form : function() {
      var $form = this.options.$content.find("form")
        , $elements = $form.find(":input:not(isolate-form *)")
        ;

      can.each($elements.toArray(), this.proxy("set_value_from_element"));
    }

  , set_value_from_element : function(el) {
      var $el = $(el)
        , name = $el.attr('name')
        , value = $el.val()
        , that = this
        ;

      // If no model is specified, short circuit setting values
      // Used to support ad-hoc form elements in confirmation dialogs
      if (!this.options.model)
        return;

      if (name)
        this.set_value({ name: name, value: value });

      if($el.is("[data-also-set]")) {
        can.each($el.data("also-set").split(","), function(oname) {
          that.set_value({ name : oname, value : value});
        });
      }
    }

  , set_value: function(item) {
    // Don't set `_wysihtml5_mode` on the instances
    if (item.name === '_wysihtml5_mode')
      return;
    var instance = this.options.instance
      , that = this;
    if(!(instance instanceof this.options.model)) {
      instance = this.options.instance
               = new this.options.model(instance && instance.serialize ? instance.serialize() : instance);
    }
    var name = item.name.split(".")
      , $elem, value, model, $other;
    $elem = this.options.$content.find("[name='" + item.name + "']:not(isolate-form *)");
    model = $elem.attr("model");

    if (model) {
      if (item.value instanceof Array)
        value = can.map(item.value, function(id) {
          return CMS.Models.get_instance(model, id);
        });
      else
        value = CMS.Models.get_instance(model, item.value);
    } else if ($elem.is("[type=checkbox]")) {
      value = $elem.is(":checked");
    } else {
      value = item.value;
    }

    if ($elem.is("[null-if-empty]") && (!value || value.length === 0))
      value = null;

    if($elem.is("[data-binding]") && $elem.is("[type=checkbox]")){
      can.map($elem, function(el){
        if(el.value != value.id)
          return;
        if($(el).is(":checked")){
          instance.mark_for_addition($elem.data("binding"), value);
        }
        else{
          instance.mark_for_deletion($elem.data("binding"), value);
        }
      });
      return;
    }
    else if($elem.is("[data-binding]")) {
      can.each(can.makeArray($elem[0].options), function(opt) {
        instance.mark_for_deletion($elem.data("binding"), CMS.Models.get_instance(model, opt.value));
      });
      if(value.push) {
        can.each(value, $.proxy(instance, "mark_for_addition", $elem.data("binding")));
      } else {
        instance.mark_for_addition($elem.data("binding"), value);
      }
    }

    if(name.length > 1) {
      if(can.isArray(value)) {
        value = new can.Observe.List(can.map(value, function(v) { return new can.Observe({}).attr(name.slice(1).join("."), v); }));
      } else {

        if($elem.is("[data-lookup]")) {
          if(!value) {
            value = null;
          } else {
            // Setting a "lookup field is handled in the autocomplete() method"
            return;
          }
        } else if(name[name.length - 1] === "date") {
          name.pop(); //date is a pseudoproperty of datetime objects
          if(!value) {
            value = null;
          } else {
            value = this.options.model.convert.date(value);
            $other = this.options.$content.find("[name='" + name.join(".") + ".time']:not(isolate-form *)");
            if($other.length) {
              value = moment(value).add(parseInt($other.val(), 10)).toDate();
            }
          }
        } else if(name[name.length - 1] === "time") {
          name.pop(); //time is a pseudoproperty of datetime objects
          value = moment(this.options.instance.attr(name.join("."))).startOf("day").add(parseInt(value, 10)).toDate();
        } else {
          value = new can.Observe({}).attr(name.slice(1).join("."), value);
        }
      }
    }

    value = value && value.serialize ? value.serialize() : value;
    if ($elem.is('[data-list]')) {
      var list_path = name.slice(0, name.length-1).join(".")
        , cur = instance.attr(list_path)
        ;
      if (!cur || !(cur instanceof can.Observe.List)) {
        instance.attr(list_path, []);
        cur = instance.attr(list_path);
      }
      value = value || [];
      cur.splice.apply(cur, [0, cur.length].concat(value));
    } else {
      if(name[0] !== "people")
        instance.attr(name[0], value);
    }
    this.setup_wysihtml5(); //in case the changes in values caused a new wysi box to appear.
  }

  , "[data-before], [data-after] change" : function(el, ev) {
    var start_date = el.datepicker('getDate');
    this.element.find("[name=" + el.data("before") + "]").datepicker({changeMonth: true, changeYear: true}).datepicker("option", "minDate", start_date);
    this.element.find("[name=" + el.data("after") + "]").datepicker({changeMonth: true, changeYear: true}).datepicker("option", "maxDate", start_date);
  }

  , "{$footer} a.btn[data-toggle='modal-submit-addmore'] click" : function(el, ev){
    this.options.attr("add_more", true);
    this.save_ui_status();
    this.triggerSave(el, ev);
  }

  , "{$footer} a.btn[data-toggle='modal-submit'] click" : function(el, ev){
    this.options.attr("add_more", false);
    this.triggerSave(el, ev);
  }

  , "{$content} a.field-hide click" : function(el, ev) { //field hide
    var $el = $(el),
      $hidable = $el.closest('[class*="span"].hidable'),
      $innerHide = $el.closest('[class*="span"]').find('.hidable'),
      $showButton = $(this.element).find('#formRestore'),
      $hideButton = $(this.element).find('#formHide');

      $el.closest('.inner-hide').addClass('inner-hidable');
      //$hidable.hide();
      $hidable.addClass("hidden");
      this.options.reset_visible = true;
      //update ui array
      var ui_unit = $hidable.find('[tabindex]');
      var i, tab_value;
      for (i = 0; i < ui_unit.length; i++) {
        tab_value = $(ui_unit[i]).attr('tabindex');
        if(tab_value > 0) {
          this.options.ui_array[tab_value-1] = 1;
          $(ui_unit[i]).attr('tabindex', '-1');
          $(ui_unit[i]).attr('uiindex', tab_value);
        }
      }

      for(var i=0; i < $el.closest('.hide-wrap.hidable').find('.inner-hidable').length; i++) {
        if(i == 1) {
          $el.closest('.inner-hide').parent('.hidable').addClass("hidden");
        }
      };

      $hideButton.fadeOut(500);
      $showButton.delay(499).fadeIn(500);

      return false;
  }

  , "{$content} #formHide click" : function(el, ev) {
    var ui_arr_length = this.options.ui_array.length;
    for(var i = 0; i < ui_arr_length; i++) {
      this.options.ui_array[i] = 0;
    }
    var $showButton = $(this.element).find('#formRestore');
    this.options.reset_visible = true;

    var $hidables = $(this.element).find(".hidable");
    $hidables.addClass("hidden");
    $(this.element).find('.inner-hide').addClass('inner-hidable');

    //Set up the hidden elements index to 1
    var hidden_elements = $hidables.find('[tabindex]');
    for(var i = 0; i < hidden_elements.length; i++) {
      var tab_value = $(hidden_elements[i]).attr('tabindex');
      //The UI array index start from 0, and tab-index/io-index is from 1
      if(tab_value > 0){
        this.options.ui_array[tab_value-1] = 1;
        $(hidden_elements[i]).attr('tabindex', '-1');
        $(hidden_elements[i]).attr('uiindex', tab_value);
      }
    }

    el.fadeOut(500);
    $showButton.delay(499).fadeIn(500);
    return false;
  }

  , "{$content} #formRestore click" : function(el, ev) {
    //Update UI status array to initial state
    var ui_arr_length = this.options.ui_array.length;
    for(var i = 0; i < ui_arr_length; i++) {
      this.options.ui_array[i] = 0;
    }

    //Set up the correct tab index for tabbing
    //Get all the ui elements with 'uiindex' set to original tabindex
    //Restore the original tab index
    var $form = $(this.element).find('form');
    var uiElements = $form.find('[uiindex]');
    for (var i = 0; i < uiElements.length; i++) {
      var $el = $(uiElements[i]);
      var tab_val = $el.attr('uiindex');
      $el.attr('tabindex', tab_val);
    }

    var $hideButton = $(this.element).find('#formHide');
    this.options.reset_visible = false;
    //$(this.element).find(".hidden").show();
    //$(this.element).find('.inner-hide').parent('.hidable').show();
    //$(this.element).find('.inner-hide').show();
    $(this.element).find(".hidden").removeClass("hidden");
    $(this.element).find('.inner-hide').removeClass('inner-hidable');
    el.fadeOut(500);
    $hideButton.delay(499).fadeIn(500);
    return false
  }

  , save_ui_status : function(){}

  , restore_ui_status : function(){
    //walk through the ui_array, for the one values,
    //select the element with tab index and hide it

    if(this.options.reset_visible){//some elements are hidden
      var $selected, str, tabindex;

      for (var i = 0; i < this.options.ui_array.length; i++){
        if(this.options.ui_array[i] == 1){
          tabindex = i+1;
          str = '[tabindex=' + tabindex + ']';
          $selected = $form.find(str);
          $selected.closest('.hidable').addClass('hidden');
          $selected.attr('uiindex', tabindex);
          $selected.attr('tabindex', '-1');
        }
      }

      if($selected){
        var $hideButton = $selected.closest('.modal-body').find('#formHide'),
          $showButton = $selected.closest('.modal-body').find('#formRestore');

        $hideButton.fadeOut(500);
        $showButton.delay(499).fadeIn(500);
      }
      return false;
    }

  }

  //make buttons non-clickable when saving
  , bindXHRToBackdrop : function(xhr, el, newtext, disable) {
      // binding of an ajax to a click is something we do manually

      var $el = $(el)
      , oldtext = $el.text();
      var alt;

      var myel = "<div ";
      //if(newtext) {
      //  $el[0].innerHTML = newtext;
      //}
      $el.addClass("disabled pending-ajax");
      if (disable !== false) {
        $el.attr("disabled", true);
      }
      xhr.always(function() {
        // If .text(str) is used instead of innerHTML, the click event may not fire depending on timing
        $el.removeAttr("disabled").removeClass("disabled pending-ajax");//[0].innerHTML = oldtext;
      });

    }

  , triggerSave : function(el, ev) {
    var ajd;
    // Normal saving process
    if (el.is(':not(.disabled)')) {
      ajd = this.save_instance(el, ev);
      if(this.options.add_more) {
        if(ajd) {
          var save_close_btn = $(this.element).find("a.btn[data-toggle=modal-submit]");
          var save_addmore_btn = $(this.element).find("a.btn[data-toggle=modal-submit-addmore]");
          var modal_backdrop = this.element.data("modal_form").$backdrop;

          $(save_addmore_btn).addClass("disabled pending-ajax");
          $(save_close_btn).addClass("disabled pending-ajax");

          this.bindXHRToBackdrop(ajd, modal_backdrop, "Saving, please wait...");
        }
      }
      else {
        if(ajd) {
          this.bindXHRToButton(ajd, el, "Saving, please wait...");
        }
      }

    }
    // Queue a save if clicked after verifying the email address
    else if (this._email_check) {
      this._email_check.done(function(data) {
        if (data.length != null)
          data = data[0];
        if (data) {
          setTimeout(function() {
            delete that._email_check;
            el.trigger('click');
          }, 0);
        }
      });
    }
  }

  , new_instance: function(data){
    var that = this,
      params = this.find_params();

    $.when(this.options.attr("instance", new this.options.model(params).attr("_suppress_errors", true)))
      .done (function() {
        // If the modal is closed early, the element no longer exists
        if (that.element) {
          var $form = $(that.element).find('form');
          $form.trigger('reset');
          // This is to trigger `focus_first_element` in modal_ajax handling
          that.element.trigger("loaded");
        }

        that.options.instance._transient || that.options.instance.attr("_transient", new can.Observe({}));
        that.options.instance.form_preload && that.options.instance.form_preload(that.options.new_object_form);
      })
      .then(this.proxy("apply_object_params"))
      .then(this.proxy("serialize_form"))
      .then(that.proxy("autocomplete"));

    this.restore_ui_status();
  }

  , "save_instance" : function(el, ev) {
      var that = this
      , instance = this.options.instance
      , ajd;


      if(instance.errors()) {
        instance.removeAttr("_suppress_errors");
        return;
      }

      this.serialize_form();

      // Special case to handle context outside the form itself
      // - this avoids duplicated change events, and the API requires
      //   `context` to be present even if `null`, unlike other attributes
      if (!instance.context)
        instance.attr('context', { id: null });

      this.disable_hide = true;
      ajd = instance.save().done(function(obj) {
        function finish() {
          delete that.disable_hide;
          if(that.options.add_more) {
            that.new_instance();
          }
          else
            that.element.trigger("modal:success", [obj, {map_and_save: $("#map-and-save").is(':checked')}]).modal_form("hide");
        }

        // If this was an Objective created directly from a Section, create a join
        var params = that.options.object_params;
        if (obj instanceof CMS.Models.Objective && params && params.section) {
          new CMS.Models.SectionObjective({
            objective: obj
            , section: CMS.Models.Section.findInCacheById(params.section.id)
            , context: { id: null }
          }).save().done(function(){
            $(document.body).trigger("ajax:flash",
                { success : "Objective mapped successfully." });
            finish();
          });
        } else {
          finish();
        }
      }).fail(function(xhr, status) {
        if(!instance.errors()) {
          $(document.body).trigger("ajax:flash", { error : xhr.responseText });
        }
        delete that.disable_hide;
      });
      return ajd;
  }

  , " ajax:flash" : function(el, ev, mesg) {
    var that = this;
    this.options.$content.find(".flash").length || that.options.$content.prepend("<div class='flash'>");

    ev.stopPropagation();

    can.each(["success", "warning", "error", "progress"], function(type) {
      var tmpl;
      if(mesg[type]) {
        tmpl = '<div class="alert alert-'
        + type
        +'"><a href="#" class="close" data-dismiss="alert">&times;</a><span>'
        + mesg[type]
        + '</span></div>';
        that.options.$content.find(".flash").append(tmpl);
      }
    });
  }

  , "{instance} destroyed" : " hide"

  , " hide" : function(el, ev) {
      if(this.disable_hide) {
        ev.stopImmediatePropagation();
        ev.stopPropagation();
        ev.preventDefault();
        return false;
      }
      if (this.options.instance) {
        delete this.options.instance._pending_joins;
      }
      if (this.options.instance instanceof can.Model
          // Ensure that this modal was hidden and not a child modal
          && ev.target === this.element[0]
          && !this.options.skip_refresh
          && !this.options.instance.isNew()) {
        this.options.instance.refresh().then(this.proxy("open_created"));
      }
    }

  , open_created : function() {
    var instance = this.options.instance;
    if (instance instanceof CMS.Models.Response) {
      // Open newly created responses
      var object_type = instance.constructor.table_singular;
      $('[data-object-id="'+instance.id+'"][data-object-type="'+object_type+'"]')
        .find('.openclose').click().openclose("open");
    }
  }

  , destroy : function() {
    if(this.options.model && this.options.model.cache) {
      delete this.options.model.cache[undefined];
    }
    this._super && this._super.apply(this, arguments);
    if(this.options.instance && this.options.instance._transient) {
      this.options.instance.removeAttr("_transient");
    }
  }
});


/*
  Below this line we're defining a can.Component, which is in this file
  because it works in tandem with the modals form controller.

  The purpose of this component is to allow for pending adds/removes of connected
  objects while the modal is visible.  On save, the actual pending actions will
  be resolved and we won't worry about the transient state we use anymore.
*/
can.Component.extend({
  tag: "ggrc-modal-connector",
  // <content> in a component template will be replaced with whatever is contained
  //  within the component tag.  Since the views for the original uses of these components
  //  were already created with content, we just used <content> instead of making
  //  new view template files.
  template: "<isolate-form><content/></isolate-form>",
  scope: {
    parent_instance: null,
    instance: null,
    instance_attr: '@',
    source_mapping: '@',
    source_mapping_source: '@',
    mapping: '@',
    attributes: {},
    // the following are just for the case when we have no object to start with,
    changes: []
  },
  events: {
    init: function() {
      var key;
      this.scope.attr("controller", this);

      if (!this.scope.instance) {
        this.scope.attr("deferred", true);
      } else if (this.scope.instance.reify) {
        this.scope.attr("instance", this.scope.instance.reify());
      }

      if (!this.scope.source_mapping) {
        this.scope.attr("source_mapping", this.scope.mapping);
      }
      if (!this.scope.source_mapping_source) {
        this.scope.source_mapping_source = 'instance';
      }

      if (this.scope[this.scope.source_mapping_source]) {
        this.scope.attr(
          "list",
          can.map(
            this.scope[this.scope.source_mapping_source].get_mapping(this.scope.source_mapping),
            function(binding) {
              return binding.instance;
            })
        );
        //this.scope.instance.attr("_transient." + this.scope.mapping, this.scope.list);
      } else {
        key = this.scope.instance_attr + "_" + (this.scope.mapping || this.scope.source_mapping);
        if(!this.scope.parent_instance._transient[key]) {
          this.scope.attr("list", []);
          this.scope.parent_instance.attr(
            "_transient." + key,
            this.scope.list
            );
        } else {
          this.scope.attr("list", this.scope.parent_instance._transient[key]);
        }
      }
      this.options.parent_instance = this.scope.parent_instance;
      this.options.instance = this.scope.instance;
      this.on();
    },

    "deferred_update": function() {
      var that = this,
          changes = this.scope.changes;

      if(changes.length > 0) {
        this.scope.attr("instance", this.scope.attr("parent_instance").attr(this.scope.instance_attr).reify());
        can.each(
          changes,
          function(item) {
            var mapping = that.scope.mapping || GGRC.Mappings.get_canonical_mapping_name(that.scope.instance.constructor.shortName, item.what.constructor.shortName);

            if(item.how === "add") {
              that.scope.instance.mark_for_addition(mapping, item.what, item.extra);
            } else {
              that.scope.instance.mark_for_deletion(mapping, item.what);
            }
          }
        );
        return that.scope.instance.constructor.resolve_deferred_bindings(that.scope.instance);
      }
    },
    "{parent_instance} updated": "deferred_update",
    "{parent_instance} created": "deferred_update",
    // this works like autocomplete_select on all modal forms and
    //  descendant class objects.
    autocomplete_select : function(el, event, ui) {
      var mapping,
          that = this,
          extra_attrs = can.reduce(
                          this.element
                          .find("input:not([data-mapping], [data-lookup])")
                          .get(),
                          function(attrs, el) {
                            attrs[$(el).attr("name")] = $(el).val();
                            return attrs;
                          }, {});
      if (that.scope.deferred) {
        that.scope.changes.push({ what: ui.item, how: "add", extra: extra_attrs });
      } else {
        mapping = that.scope.mapping || GGRC.Mappings.get_canonical_mapping_name(that.scope.instance.constructor.shortName, ui.item.constructor.shortName);
        that.scope.instance.mark_for_addition(mapping, ui.item, extra_attrs);
      }
      that.scope.list.push(ui.item);
      that.scope.attr("show_new_object_form", false);
    },
    "[data-toggle=unmap] click" : function(el, ev) {
      var i, that = this;
      ev.stopPropagation();
      can.map(
        el.find('.result'),
        function(result_el) {
          var mapping,
              obj = $(result_el).data("result");
          if (that.scope.deferred) {
            that.scope.changes.push({ what: obj, how: "remove" });
          } else {
            mapping = that.scope.mapping || GGRC.Mappings.get_canonical_mapping_name(that.scope.instance.constructor.shortName, obj.constructor.shortName);
            that.scope.instance.mark_for_deletion(mapping, obj);
          }
          for(i = that.scope.list.length; i >= 0; i--) {
            if(that.scope.list[i] === obj) {
              that.scope.list.splice(i, 1);
            }
          }
        });
    },
    "input[null-if-empty] change" : function(el) {
      if (!el.val()) {
        this.scope.attributes.attr(el.attr("name"), null);
      }
    },
    "input keyup" : function(el, ev) {
      ev.stopPropagation();
    },
    "input, textarea, select change" : function(el, ev) {
        this.scope.attributes.attr(el.attr("name"), el.val());
    },

    "input:not([data-lookup], [data-mapping]), textarea keyup" : function(el, ev) {
      if (el.prop('value').length == 0 ||
        (typeof el.attr('value') !== 'undefined' && el.attr('value').length == 0)) {
        this.scope.attributes.attr(el.attr("name"), el.val());
      }
    },
    "a[data-toggle=submit]:not(.disabled) click": function(el, ev) {
      var obj, mapping,
          that = this,
          binding = this.scope.instance.get_binding(this.scope.mapping),
          extra_attrs = can.reduce(
                          this.element
                          .find("input:not([data-mapping], [data-lookup])")
                          .get(),
                          function(attrs, el) {
                            if ($(el).attr("model")) {
                              attrs[$(el).attr("name")] = CMS.Models[$(el).attr("model")].findInCacheById($(el).val());
                            } else {
                              attrs[$(el).attr("name")] = $(el).val();
                            }
                            return attrs;
                          }, {});

      ev.stopPropagation();

      extra_attrs[binding.loader.object_attr] = this.scope.instance;
      if(binding.loader instanceof GGRC.ListLoaders.DirectListLoader) {
        obj = new CMS.Models[binding.loader.model_name](extra_attrs);
      } else {
        obj = new CMS.Models[binding.loader.option_model_name](extra_attrs);
      }

      if (that.scope.deferred) {
        that.scope.changes.push({ what: obj, how: "add", extra: extra_attrs });
      } else {
        mapping = that.scope.mapping || GGRC.Mappings.get_canonical_mapping_name(that.scope.instance.constructor.shortName, obj.constructor.shortName);
        that.scope.instance.mark_for_addition(mapping, obj, extra_attrs);
      }
      that.scope.list.push(obj);
      that.scope.attr("attributes", {});
    },
    "a[data-object-source] modal:success": function(el, ev, data) {
      var mapping,
          that = this;
      ev.stopPropagation();

      can.each(data.arr || [data], function(obj) {

        if (that.scope.deferred) {
          that.scope.changes.push({ what: obj, how: "add" });
        } else {
          mapping = that.scope.mapping || GGRC.Mappings.get_canonical_mapping_name(that.scope.instance.constructor.shortName, obj.constructor.shortName);
          that.scope.instance.mark_for_addition(mapping, obj);
        }
        that.scope.list.push(obj);
      });
    },
    ".ui-autocomplete-input modal:success" : function(el, ev, data, options) {
      var that = this,
          extra_attrs = can.reduce(
                          this.element
                          .find("input:not([data-mapping], [data-lookup])")
                          .get(),
                          function(attrs, el) {
                            if ($(el).attr("model")) {
                              attrs[$(el).attr("name")] = CMS.Models[$(el).attr("model")].findInCacheById($(el).val());
                            } else {
                              attrs[$(el).attr("name")] = $(el).val();
                            }
                            return attrs;
                          }, {});

      can.each(data.arr || [data], function(obj) {
        var mapping;
        if (that.scope.deferred) {
          that.scope.changes.push({ what: obj, how: "add", extra: extra_attrs });
        } else {
          mapping = that.scope.mapping || GGRC.Mappings.get_canonical_mapping_name(that.scope.instance.constructor.shortName, obj.constructor.shortName);
          that.scope.instance.mark_for_addition(mapping, obj, extra_attrs);
        }
        that.scope.list.push(obj);
        that.scope.attr("attributes", {});
      });
    }
  },
  helpers: {
    // Mapping-based autocomplete selectors use this helper to
    //  attach the mapping autocomplete ui widget.  These elements should
    //  be decorated with data-mapping attributes.
    mapping_autocomplete : function(options) {
      return function(el) {
        var $el = $(el);
        $el.ggrc_mapping_autocomplete({
          controller : options.contexts.attr("controller"),
          model : $el.data("model"),
          mapping : false
        });
      };
    }
  },
});




})(window.can, window.can.$);
