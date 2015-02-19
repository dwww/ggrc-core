/*!
    Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
    Created By: anze@reciprocitylabs.com
    Maintained By: anze@reciprocitylabs.com
*/


can.Control("CMS.Controllers.InfoPin", {
  defaults: {
    view: GGRC.mustache_path + "/base_objects/info.mustache"
  }
}, {
  init: function(el, options) {
    var instance = GGRC.page_instance();
    this.element.height(0);
  },
  findView: function(instance) {
    var view = instance.class.table_plural + "/info";

    if (instance instanceof CMS.Models.Person) {
      view = GGRC.mustache_path + "/ggrc_basic_permissions/people_roles/info.mustache";
    } else if (instance instanceof CMS.Models.Response) {
      view = GGRC.mustache_path + "/responses/info.mustache";
    } else if (view in GGRC.Templates) {
      view = GGRC.mustache_path + "/" + view + ".mustache";
    } else {
      view = this.options.view;
    }
    return view;
  },
  findOptions: function(el) {
    var tree_node = el.closest('.cms_controllers_tree_view_node').control();
    return tree_node.options;
  },
  loadChildTrees: function() {
    var child_tree_dfds = []
      , that = this
      ;

    this.element.find('.' + CMS.Controllers.TreeView._fullName).each(function(_, el) {
      var $el = $(el)
        , child_tree_control
        ;

      //  Ensure this targets only direct child trees, not sub-tree trees
      if ($el.closest('.' + that.constructor._fullName).is(that.element)) {
        child_tree_control = $el.control();
        if (child_tree_control)
          child_tree_dfds.push(child_tree_control.display());
      }
    });
  },
  unsetInstance: function() {
    this.element.html('');
    this.element.height(0);
    $('.cms_controllers_tree_view_node').removeClass('active');
    $(window).trigger('resize');
  },
  setInstance: function(instance, el) {
    var options = this.findOptions(el),
        view = this.findView(instance);

    this.element.html(can.view(view, {
      instance: instance,
      model: instance.class,
      is_info_pin: true,
      options: options,
      result: options.result
    }));

    // Load trees inside info pin
    this.loadChildTrees();

    // Make sure pin is visible
    if (!this.element.height()) {
      this.element.animate({ height: $(window).height() / 3 }, {
        duration: 800,
        easing: 'easeOutExpo',
        complete: function () {
          $(window).trigger('resize');
          el[0].scrollIntoView(false);
        }
      });
    }else{
      el[0].scrollIntoView(false);
    }
  },
  '.pin-action a click': function(el) {
    var options = {
        duration: 800,
        easing: 'easeOutExpo'
      },
      $info = this.element.find('.info'),
      win_height = $(window).height(),
      target_height;

    this.element.find('.pin-action i').css({'opacity': 0.25});

    if (el.hasClass('min')) {
      target_height = 75;
    } else if (el.hasClass('max')) {
      target_height = win_height * 3 / 4;
    } else {
      target_height = win_height / 3;
    }

    if (target_height < $info.height()) {
      options.start = function () {
        $(window).trigger("resize", target_height);
      };
    }else{
      options.complete = function () {
        $(window).trigger("resize");
      };
    }

    this.element.animate({height: target_height}, options);
    el.find('i').css({'opacity':1});
  }
});
