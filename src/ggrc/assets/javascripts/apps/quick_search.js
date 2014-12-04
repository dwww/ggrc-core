/*!
    Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
    Created By: brad@reciprocitylabs.com
    Maintained By: brad@reciprocitylabs.com
*/

//= require can.jquery-all
//= require controllers/quick_search_controller
(function(namespace, $) {

$(function() {
  $("#lhn").cms_controllers_lhn();

  $(document.body).on("click", "a[data-toggle=unmap]", function(ev) {
    var $el = $(this)
      ;
    //  Prevent toggling `openclose` state in trees
    ev.stopPropagation();
    $el.fadeTo('fast', 0.25);
    $el.children(".result").each(function(i, result_el) {
      var $result_el = $(result_el)
        , result = $result_el.data('result')
        , mappings = result && result.get_mappings()
        , i
        ;
      
      function notify(instance){
        $(document.body).trigger(
            "ajax:flash"
            , {"success" : "Unmap successful."}
          );
      }
      
      can.each(mappings, function(mapping) {
        mapping.refresh().done(function() {
          if (mapping instanceof CMS.Models.Control) {
            mapping.removeAttr('directive');
            mapping.save().then(notify);
          }
          else {
            mapping.destroy().then(notify);
          }
        });
      });
    });
  });

  $(document.body).on("click", ".map-to-page-object", function(ev) {
    //  Prevent toggling `openclose` state in trees
    ev.stopPropagation();

    var i, v, $target = $(ev.currentTarget)
    , follow = $target.data("follow")
    , inst = Mustache.resolve($target.data("instance"))
    , page_model = GGRC.infer_object_type(GGRC.page_object)
    , page_instance = GGRC.page_instance()
    //, link = page_model.links_to[inst.constructor.model_singular]
    , params = {}
    , mappings = Mustache.resolve($target.data("existing_mappings"));

    if(can.isArray(inst) || inst instanceof can.List) {
      if(mappings) {
        mappings = can.map(mappings, function(m) {
          return m.instance || m;
        });
      }

      for(i = 0; i < inst.length; i++) {
        v = inst[i].instance || inst[i];
        if(page_instance !== v && (!mappings || !~can.inArray(v, mappings))) {
          $target.data("instance", v);
          arguments.callee.call(this, ev);
        }
      }
      $target.data("instance", inst);
      return;
    }

    if(typeof link === "string") {
      link = GGRC.Models[link] || CMS.Models[link];
    }

    function triggerFlash(type) {
      $target.trigger(
        "ajax:flash"
        , type === "error" 
          ? {
            error : [
              "Failed to map"
              , inst.constructor.title_singular
              , "<strong>"
              , inst.title
              , "</strong> to"
              , page_model.title_singular
              , "<strong>"
              , page_instance.title
              , "</strong>"
              ].join(" ")
            }
          : {
            success : [
              "Mapped"
              , inst.constructor.title_singular
              , "<strong>"
              , inst.title
              , "</strong> to"
              , page_model.title_singular
              , "<strong>"
              , page_instance.title
              , "</strong>"
              ].join(" ")
            }
        );

      // Switch the active widget view if 'data-follow' was specified
      if (follow && type !== "error") {
        window.location.hash = '#' + inst.constructor.root_object + '_widget';
        $('a[href="' + window.location.hash + '"]').trigger("click");
      }
    }

    var join_context;
    if (inst instanceof CMS.Models.Program && inst.context) {
      join_context = { id : inst.context.id };
    } else {
      join_context = page_instance.context || { id : null };
    }
    join_object = GGRC.Mappings.make_join_object(
        page_instance, inst, { context : join_context });
    // Map the object if we're able to
    if (join_object) {
      join_object.save()
        .done(triggerFlash)
        .fail(function(xhr) {
          // Currently, the only error we encounter here is uniqueness
          // constraint violations.  Let's use a nicer message!
          var message = "That object is already mapped";
          $(document.body).trigger("ajax:flash", { error: message });
        });
    }
    // Otherwise throw a warning
    else {
      triggerFlash("error");
    }

  });

});

})(this, jQuery);
