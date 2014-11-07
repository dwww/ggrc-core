/*!
    Copyright (C) 2013 Google Inc., authors, and contributors <see AUTHORS file>
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
    Created By: brad@reciprocitylabs.com
    Maintained By: brad@reciprocitylabs.com
*/

var GGRC = window.GGRC || {};
GGRC.mustache_path = '/static/mustache';

GGRC.hooks = GGRC.hooks || {};
GGRC.register_hook = function(path, hook) {
  var h, parent_path, last;
  parent_path = path.split(".");
  last = parent_path.pop();
  parent_path = can.getObject(parent_path.join("."), GGRC.hooks, true);
  if(!(h = parent_path[last])) {
    h = new can.Observe.List();
    parent_path[last] = h;
  }
  h.push(hook);
};

GGRC.current_url_compute = can.compute(function() {
  var path = window.location.pathname
  , fragment = window.location.hash;
  return window.encodeURIComponent(path + fragment);
});

$(window).on('hashchange', function() {
  GGRC.current_url_compute(window.location);
});

jQuery.migrateMute = true; //turn off console warnings for jQuery-migrate


GGRC.extensions = GGRC.extensions || [];

GGRC.extensions.push({
    name: "core"

  , object_type_decision_tree: function() {
      return {
        "program" : CMS.Models.Program
      , "audit" : CMS.Models.Audit
      /*, "directive" : {
        _discriminator: function(data) {
          var model_i, model;
          models =  [CMS.Models.Regulation, CMS.Models.Policy, CMS.Models.Contract];
          for (model_i in models) {
            model = models[model_i];
            if (model.meta_kinds.indexOf(data.kind) >= 0) {
              return model;
            }
          }
          throw new ModelError("Invalid Directive#kind value '" + data.kind + "'", data);
        }
      }*/
      , "contract" : CMS.Models.Contract
      , "policy" : CMS.Models.Policy
      , "standard" : CMS.Models.Standard
      , "regulation" : CMS.Models.Regulation
      , "org_group" : CMS.Models.OrgGroup
      , "vendor" : CMS.Models.Vendor
      , "project" : CMS.Models.Project
      , "facility" : CMS.Models.Facility
      , "product" : CMS.Models.Product
      , "data_asset" : CMS.Models.DataAsset
      , "market" : CMS.Models.Market
      , "system_or_process" : {
        _discriminator: function(data) {
          if (data.is_biz_process)
            return CMS.Models.Process;
          else
            return CMS.Models.System;
        }
      }
      , "system" : CMS.Models.System
      , "process" : CMS.Models.Process
      , "control" : CMS.Models.Control
      , "objective" : CMS.Models.Objective
      , "section" : CMS.Models.Section
      , "clause" : CMS.Models.Clause
      , "section_objective" : CMS.Models.SectionObjective
      , "person" : CMS.Models.Person
      , "role" : CMS.Models.Role
      , "threat" : CMS.Models.Threat
      , "vulnerability" : CMS.Models.Vulnerability
      , "template" : CMS.Models.Template
      }
    }
});


function ModelError(message, data) {
  this.name = "ModelError";
  this.message = message || "Invalid Model encountered";
  this.data = data;
}
ModelError.prototype = Error.prototype;

  window.cms_singularize = function(type) {
    type = type.trim();
    var _type = type.toLowerCase();
    switch(_type) {
      case "facilities":
      type = type[0] + "acility"; break;
      case "people":
      type = type[0] + "erson"; break;
      case "processes":
      type = type[0] + "rocess"; break;
      case "policies":
      type = type[0] + "olicy"; break;
      case "systems_processes":
      type = type[0] + "ystem_" + type[8] + "rocess";
      break;
      default:
      type = type.replace(/s$/, "");
    }

    return type;
  };


  window.calculate_spinner_z_index = function() {
    var zindex = 0;
    $(this).parents().each(function() {
      var z = parseInt($(this).css("z-index"), 10);
      if(z) {
        zindex = z;
        return false;
      }
    });
    return zindex + 10;
  };

(function(can) {
  can.Construct("PersistentNotifier", {
    defaults : {
      one_time_cbs : true
      , while_queue_has_elements : function() {}
      , when_queue_empties : function() {}
    }
  }, {
    init : function(options) {
      var that = this;
      this.dfds = [];
      this.list_empty_cbs = [];
      can.each(this.constructor.defaults, function(val, key) {
          that[key] = val;
      });
      can.each(options, function(val, key) {
        that[key] = val;
      });
    }
    , queue : function(dfd) {
      var idx
      , oldlen = this.list_empty_cbs.length
      , that = this;
      if(!dfd || !dfd.then) {
        throw "ERROR: attempted to queue something other than a Deferred or Promise";
      }
      idx = this.dfds.indexOf(dfd);

      if(!~idx) { //enforce uniqueness
        this.dfds.push(dfd);
        dfd.always(function() {
          var i = that.dfds.indexOf(dfd);
          ~i && that.dfds.splice(i, 1);
          if(that.dfds.length < 1) {
            can.each(that.list_empty_cbs, Function.prototype.call);
            if(that.one_time_cbs) {
              that.list_empty_cbs = [];
            }
            that.when_queue_empties();
          }
        });
      }
      if(oldlen < 1 && that.dfds.length > 0) {
        that.while_queue_has_elements();
      }
    }
    , on_empty : function(fn) {
      if(!this.one_time_cbs || this.dfds.length < 1) {
        fn();
      }
      if((this.dfds.length > 0 || !this.one_time_cbs) && !~this.list_empty_cbs.indexOf(fn)) {
          this.list_empty_cbs.push(fn);
      }
    }
    , off_empty : function(fn) {
      var idx;
      if(~(idx = this.list_empty_cbs.indexOf(fn)))
        this.list_empty_cbs.splice(idx, 1);
    }
  });
})(this.can);

(function(GGRC) {
var confirmleaving = function confirmleaving() {
  return window.confirm("There are operations in progress.  Are you sure you want to leave the page?");
}
, notifier = new PersistentNotifier({
  while_queue_has_elements : function() {
    $(window).on("unload", confirmleaving);
  }
  , when_queue_empties : function() {
    $(window).off("unload", confirmleaving);
  }
  , name : "GGRC/window"
});

jQuery.extend(GGRC, {
    get_object_type_decision_tree: function() {
      var tree = {}
        , extensions = GGRC.extensions || []
        ;

      can.each(extensions, function(extension) {
        if (extension.object_type_decision_tree) {
          if (can.isFunction(extension.object_type_decision_tree)) {
            $.extend(tree, extension.object_type_decision_tree());
          } else {
            $.extend(tree, extension.object_type_decision_tree);
          }
        }
      });

      return tree;
    }

  , infer_object_type : function(data) {
    var decision_tree = GGRC.get_object_type_decision_tree();

    function resolve_by_key(subtree, data) {
      var kind = data[subtree._key];
      var model;
      can.each(subtree, function (v,k) {
        if (k != "_key" && v.meta_kinds.indexOf(kind) >= 0) {
          model = v;
        }
      });
      return model;
    }

    function resolve(subtree, data) {
      if(typeof subtree === "undefined")
        return null;
      return can.isPlainObject(subtree) ?
        subtree._discriminator(data) :
        subtree;
    }

    if(!data) {
      return null;
    } else {
      return can.reduce(Object.keys(data), function(a, b) {
        return a || resolve(decision_tree[b], data[b]);
      }, null);
    }
  }
  , make_model_instance : function(data) {
    if(!data) {
      return null;
    } else if(!!GGRC.page_model && GGRC.page_object === data) {
      return GGRC.page_model;
    } else {
      return GGRC.page_model = GGRC.infer_object_type(data).model($.extend({}, data));
    }
  }

  , page_instance : function() {
    if (!GGRC._page_instance && GGRC.page_object) {
      GGRC._page_instance = GGRC.make_model_instance(GGRC.page_object);
    }
    return GGRC._page_instance;
  }

  , eventqueue: []
  , eventqueueTimeout: null
  , eventqueueTimegap: 20 //ms

  , queue_exec_next: function() {
      var fn = GGRC.eventqueue.shift();
      if (fn)
        fn();
      if (GGRC.eventqueue.length > 0)
        GGRC.eventqueueTimeout =
          setTimeout(GGRC.queue_exec_next, GGRC.eventqueueTimegap);
      else
        GGRC.eventqueueTimeout = null;
    }

  , queue_event : function(events) {
      if (typeof(events) === "function")
        events = [events];
      GGRC.eventqueue.push.apply(GGRC.eventqueue, events);
      if (!GGRC.eventqueueTimeout)
        GGRC.eventqueueTimeout =
          setTimeout(GGRC.queue_exec_next, GGRC.eventqueueTimegap);
    }

  , navigate : function(url) {
    function go() {
      if(!url) {
        window.location.reload();
      } else {
        window.location.assign(url);
      }
    }
    notifier.on_empty(go);
  }

  , delay_leaving_page_until : $.proxy(notifier, "queue")
});

/*
  The GGRC Math library provides basic arithmetic across arbitrary precision numbers represented
  as strings.  We wrote this initially to handle easy re-sorting of items in tree views, since
  we could easily get hundreds of re-sorts by halving the distance from zero to MAX_SAFE_INT
  until we got down to 10^-250 which would overflow the string on the data side with zeroes.
*/
GGRC.Math =  GGRC.Math || {};
$.extend(GGRC.Math, {
  /*
    @param a an addend represented as a decimal notation string
    @param b an addend represented as a decimal notation string

    @return the sum of the numbers represented in a and b, as a decimal notation string.
  */
  string_add: function(a, b) {
    var _a, _b, i, _c = 0,
        ret = [],
        adi = a.indexOf("."),
        bdi = b.indexOf(".");

    if (adi < 0) {
      a = a + ".";
      adi = a.length - 1;
    }
    if (bdi < 0) {
      b = b + ".";
      bdi = b.length - 1;
    }
    while (adi < bdi) {
      a = "0" + a;
      adi++;
    }
    while (bdi < adi) {
      b = "0" + b;
      bdi++;
    }

    for (i = Math.max(a.length, b.length) - 1; i >= 0; i--) {
      _a = a[i] || 0;
      _b = b[i] || 0;
      if (_a === "." || _b === ".") {
        if (_a !== "." || _b !== ".")
          throw "Decimal alignment error";
        ret.unshift(".");
      } else {
        ret.unshift((+_a) + (+_b) + _c);
        _c = Math.floor(ret[0] / 10);
        ret[0] = (ret[0] % 10).toString(10);
      }
    }
    if (_c > 0) {
      ret.unshift(_c.toString(10));
    }
    if (ret[ret.length - 1] === ".") {
      ret.pop();
    }
    return ret.join("");
  },

  /*
    @param a a decimal notation string

    @return one half of the number represented in a, as a decimal notation string.
  */
  string_half: function(a) {
    var i, _a, _c = 0, ret = [];

    if (!~a.indexOf(".")) {
      a = a + ".";
    }
    for (i = 0; i < a.length; i++) {
      _a = a[i];
      if (_a === ".") {
        ret.push(".");
      } else {
        _a = Math.floor((+_a + _c) / 2);
        if (+a[i] % 2) {
          _c = 10;
        } else {
          _c = 0;
        }
        ret.push(_a.toString(10));
      }
    }
    if (_c > 0) {
      ret.push("5");
    }
    if (ret[ret.length - 1] === ".") {
      ret.pop();
    }
    while (ret[0] === "0" && ret.length > 1) {
      ret.shift();
    }
    return ret.join("");
  },

  /*
    @param a a number represented as a decimal notation string
    @param b a number represented as a decimal notation string

    @return the maximum of the numbers represented in a and b, as a decimal notation string.
  */
  string_max: function(a, b) {
    return this.string_less_than(a, b) ? b : a;
  },

  /*
    @param a a number represented as a decimal notation string
    @param b a number represented as a decimal notation string

    @return true if the number represented in a is less than that in b, false otherwise
  */
  string_less_than: function(a, b) {
    var i,
        _a = ("" + a).replace(/^0*/, ""),
        _b = ("" + b).replace(/^0*/, ""),
        adi = _a.indexOf("."),
        bdi = _b.indexOf(".");

    if (adi < 0) {
      _a = _a + ".";
      adi = _a.length - 1;
    }
    if (bdi < 0) {
      _b = _b + ".";
      bdi = _b.length - 1;
    }
    if (adi < bdi) {
      return true;
    }
    if (bdi < adi) {
      return false;
    }
    for (i = 0; i < _a.length - 1; i++) {
      if (_a[i] === ".") {
        // continue
      } else {
        if ((+_a[i] || 0) < (+_b[i] || 0)) {
          return true;
        } else if ((+_a[i] || 0) > (+_b[i] || 0)) {
          return false;
        }
      }
    }
    return _b.length >= _a.length ? false : true;
  }

});

})(GGRC);


(function($){

// Set up all PUT requests to the server to respect ETags, to ensure that
//  we are not overwriting more recent data than was viewed by the user.
var etags = {};
$.ajaxPrefilter(function( options, originalOptions, jqXHR ) {
  var data = originalOptions.data;

  function attach_provisional_id(prop) {
    jqXHR.done(function(obj) {
      obj[prop].provisional_id = data[prop].provisional_id;
    });
  }

  if ( /^\/api\//.test(options.url) && /PUT|POST|DELETE/.test(options.type.toUpperCase())) {
    options.dataType = "json";
    options.contentType = "application/json";
    jqXHR.setRequestHeader("If-Match", (etags[originalOptions.url] || [])[0]);
    jqXHR.setRequestHeader("If-Unmodified-Since", (etags[originalOptions.url] || [])[1]);
    options.data = options.type.toUpperCase() === "DELETE" ? "" : JSON.stringify(data);
    for(var i in data) {
      if(data.hasOwnProperty(i) && data[i] && data[i].provisional_id) {
        attach_provisional_id(i);
      }
    }
  }
  if( /^\/api\//.test(options.url) && (options.type.toUpperCase() === "GET")) {
    options.cache = false;
  }
  if( /^\/api\/\w+/.test(options.url)) {
    jqXHR.setRequestHeader("X-Requested-By", "gGRC");
    jqXHR.done(function(data, status, xhr) {
      if(!/^\/api\/\w+\/\d+/.test(options.url) && options.type.toUpperCase() === "GET")
        return;
      switch(options.type.toUpperCase()) {
        case "GET":
        case "PUT":
          etags[originalOptions.url] = [xhr.getResponseHeader("ETag"), xhr.getResponseHeader("Last-Modified")];
          break;
        case "POST":
          for(var d in data) {
            if(data.hasOwnProperty(d) && data[d].selfLink) {
              etags[data[d].selfLink] = [xhr.getResponseHeader("ETag"), xhr.getResponseHeader("Last-Modified")];
            }
          }
          break;
        case "DELETE":
          delete etags[originalOptions.url];
          break;
      }
    });
  }
});

//Set up default failure callbacks if nonesuch exist.
  var _old_ajax = $.ajax;

  var statusmsgs = {
    401 : "The server says you are not authorized.  Are you logged in?"
    , 409 : "There was a conflict in the object you were trying to update.  The version on the server is newer."
    , 412 : "One of the form fields isn't right.  Check the form for any highlighted fields."
  };


  // Here we break the deferred pattern a bit by piping back to original AJAX deferreds when we
  // set up a failure handler on a later transformation of that deferred.  Why?  The reason is that
  //  we have a default failure handler that should only be called if no other one is registered,
  //  unless it's also explicitly asked for.  If it's registered in a transformed one, though (after
  //  then() or pipe()), then the original one won't normally be notified of failure.
  can.ajax = $.ajax = function(options) {
    var _ajax = _old_ajax.apply($, arguments);

    function setup(_new_ajax, _old_ajax) {
      var _old_then = _new_ajax.then;
      var _old_fail = _new_ajax.fail;
      var _old_pipe = _new_ajax.pipe;
      _old_ajax && (_new_ajax.hasFailCallback = _old_ajax.hasFailCallback);
      _new_ajax.then = function() {
        var _new_ajax = _old_then.apply(this, arguments);
        if(arguments.length > 1) {
          this.hasFailCallback = true;
          if(_old_ajax)
            _old_ajax.fail(function() {});
        }
        setup(_new_ajax, this);
        return _new_ajax;
      };
      _new_ajax.fail = function() {
        this.hasFailCallback = true;
        if(_old_ajax)
          _old_ajax.fail(function() {});
        return _old_fail.apply(this, arguments);
      };
      _new_ajax.pipe = function() {
        var _new_ajax = _old_pipe.apply(this, arguments);
        setup(_new_ajax, this);
        return _new_ajax;
      };
    }

    setup(_ajax);
    return _ajax;
  };

  $(document).ajaxError(function(event, jqxhr, settings, exception) {
    if(!jqxhr.hasFailCallback || settings.flashOnFail || (settings.flashOnFail == null && jqxhr.flashOnFail)) {
      // TODO: Import produced 'canceled' ajax flash message that needed handling. Will refactor once better method works.
      if (settings.url.indexOf("import") == -1 || exception !== 'canceled') {
        $(document.body).trigger(
          "ajax:flash"
          , {"error" : jqxhr.getResponseHeader("X-Flash-Error") || statusmsgs[jqxhr.status] || exception.message || exception}
        );
      }
    }
  });
})(jQuery);

// dismiss non-expandable success flash messages
$(document).ready(function() {
  // monitor target, where flash messages are added
  var target = $('section.content div.flash')[0];
  var observer = new MutationObserver(function( mutations ) {
    mutations.forEach(function( mutation ) {
      // check for new nodes
      if( mutation.addedNodes !== null ) {
        // remove the success message from non-expandable
        // flash success messages after five seconds
        setTimeout(function() {
          $('.flash .alert-success').not(':has(ul.flash-expandable)').remove();
        }, 5000);
      }
    });
  });

  var config = {
      attributes: true
    , childList: true
    , characterData: true
  };

  if (target) {
    observer.observe(target, config);
  }
});


//remove flash messages generated by python
$(document).ready(function() {
  setTimeout(function() {
    $('.flash .alert-success').not(':has(ul.flash-expandable)').remove();
  }, 5000);
});


jQuery(document).ready(function($) {
  // TODO: Not AJAX friendly
  $('.bar[data-percentage]').each(function() {
    $(this).css({ width: $(this).data('percentage') + '%' });
  });
});

jQuery(document).ready(function($) {
  // Monitor Bootstrap Tooltips to remove the tooltip if the triggering element
  // becomes hidden or removed.
  //
  // * $currentTip needed because tooltips don't fire events until Bootstrap
  //   2.3.0 and $currentTarget.tooltip('hide') doesn't seem to work when it's
  //   not in the DOM
  // * $currentTarget.data('tooltip-monitor') is a flag to ensure only one
  //   monitor per element
  function monitorTooltip($currentTarget) {
    var monitorFn
      , monitorPeriod = 500
      , monitorTimeoutId = null
      , $currentTip
      , dataTooltip;

    if (!$currentTarget.data('tooltip-monitor')) {
      dataTooltip = $currentTarget.data('tooltip');
      $currentTip = dataTooltip && dataTooltip.$tip;

      monitorFn = function() {
        dataTooltip = dataTooltip || $currentTarget.data('tooltip');
        $currentTip = $currentTip || (dataTooltip && dataTooltip.$tip);

        if (!$currentTarget.is(':visible')) {
          $currentTip && $currentTip.remove();
          $currentTarget.data('tooltip-monitor', false);
        } else if ($currentTip && $currentTip.is(':visible')) {
          monitorTimeoutId = setTimeout(monitorFn, monitorPeriod);
        } else {
          $currentTarget.data('tooltip-monitor', false);
        }
      };

      monitorTimeoutId = setTimeout(monitorFn, monitorPeriod);
      $currentTarget.data('tooltip-monitor', true);
    }
  };

  $('body').on('shown', '.modal', function() {
    $('.tooltip').hide();;
  });

  // Fix positioning of bootstrap tooltips when on left/right edge of screen
  // Possibly remove this when upgrade to Bootstrap 2.3.0 (which has edge detection)
  var _tooltip_show = $.fn.tooltip.Constructor.prototype.show;
  $.fn.tooltip.Constructor.prototype.show = function() {
    var margin = 10
      , container_width = document.width
      , tip_pos, $arrow, offset, return_value;

    _tooltip_show.apply(this);

    return_value = this.$tip.css({ 'white-space': 'normal' });

    tip_pos = this.$tip.position();
    tip_pos.width = this.$tip.width();
    tip_pos.height = this.$tip.height();
    $arrow = this.$tip.find('.tooltip-arrow');

    offset = tip_pos.left + tip_pos.width - container_width + margin;
    if (offset > 0) {
      this.$tip.css({ left: tip_pos.left - offset });
      $arrow.css({ left: parseInt($arrow.css('left')) + offset });
    } else if (tip_pos.left < margin) {
      this.$tip.css({ left: margin });
      $arrow.css({ left: parseInt($arrow.css('left')) + tip_pos.left - margin });
    }

    return return_value;
  };

  // Listeners for initial tooltip mouseovers
  $('body').on('mouseover', '[data-toggle="tooltip"], [rel=tooltip]', function(e) {
    var $currentTarget = $(e.currentTarget);

    if (!$currentTarget.data('tooltip')) {
      $currentTarget
        .tooltip({ delay: {show : 500, hide : 0} })
        .triggerHandler(e);
    }

    monitorTooltip($currentTarget);
  });
});

// Setup for Popovers
jQuery(document).ready(function($) {
  var defaults = {
    delay: {show : 500, hide : 100},
    placement: 'left',
    content: function(trigger) {
      var $trigger = $(trigger);

      var $el = $(new Spinner().spin().el);
      $el.css({
        width: '100px',
        height: '100px',
        left: '50px',
        top: '50px',
        zIndex : calculate_spinner_z_index
       });
      return $el[0];
    }
  };

  // Listeners for initial mouseovers for stick-hover
  $('body').on('mouseover', '[data-popover-trigger="sticky-hover"]', function(e) {
    // If popover instance doesn't exist already, create it and
    // force the 'enter' event.
    if (!$(e.currentTarget).data('sticky_popover')) {
      $(e.currentTarget)
        .sticky_popover($.extend({}, defaults, {
          trigger: 'sticky-hover'
          , placement : function() {
            var $el = this.$element
              , spaceLeft = $(document).width() - ($el.offset().left + $el.width())
              , spaceRight = $el.offset().left
              , popover_size = 620;
            // Display on right if there is enough space
            if($el.closest(".widget-area:first-child").length && spaceLeft > popover_size)
              return "right";
            else if(spaceRight > popover_size){
              return "left";
            }
            return "top";
          }
        }))
        .triggerHandler(e);
    }
  });

  // Listeners for initial clicks for popovers
  $('body').on('click', 'a[data-popover-trigger="click"]', function(e) {
    e.preventDefault();
    if (!$(e.currentTarget).data('sticky_popover')) {
      $(e.currentTarget)
        .sticky_popover($.extend({}, defaults, { trigger: 'click' }))
        .triggerHandler(e);
    }
  });

  function showhide(upsel, downsel) {
    return function(command) {
      $(this).each(function() {
        var $this = $(this)
            , $content = $this.closest(upsel).find(downsel)
            , cmd = command;

        if(typeof cmd !== "string" || cmd === "toggle") {
          cmd = $this.hasClass("active") ? "hide" : "show";
        }

        if(cmd === "hide") {
          $content.slideUp();
          $this.removeClass("active");
        } else if(cmd === "show") {
          $content.slideDown();
          $this.addClass("active");
        }
      });

      return this;
    };
  }

  $.fn.showhide = showhide(".widget", ".content, .filter");
  $.fn.modal_showhide = showhide(".modal", ".hidden-fields-area");
  $('body').on('click', ".expand-link a", $.fn.modal_showhide);

  $.fn.widget_showhide = showhide(".info", ".hidden-fields-area");
  $('body').on('click', ".info-expand a", $.fn.widget_showhide);

  // Show/hide tree leaf content
  $('body').on('click', '.tree-structure .oneline, .tree-structure .description, .tree-structure .view-more', oneline);

  function oneline(command) {
    $(this).each(function() {
      var $this = $(this)
        , $leaf = $this.closest('[class*=span]').parent().children("[class*=span]:first")
        , $title = $leaf.find('.oneline')
        , $description = $leaf.find('.description')
        , $view = $leaf.closest('.row-fluid').find('.view-more')
        , cmd = command
        ;

      if ($description.length > 0) {
        if(typeof cmd !== "string") {
          cmd = $description.hasClass("in") ? "hide" : "view";
        }

        if(cmd === "view") {
          $description.addClass('in');
          $title.find('.description-inline').addClass('out');
          if ($title.is('.description-only')) {
            $title.addClass('out');
          }
          $view.text('hide');
        } else if(cmd === "hide") {
          $description.removeClass('in');
          $title.find('.description-inline').removeClass('out');
          if ($title.is('.description-only')) {
            $title.removeClass('out');
          }
          $view.text('view');
        }
      }
    });

    return this;
  }

  $.fn.oneline = oneline;

  // Close other popovers when one is shown
  $('body').on('show.popover', function(e) {
    $('[data-sticky_popover]').each(function() {
      var popover = $(this).data('sticky_popover');
      popover && popover.hide();
    });
  });

  // Close all popovers on custom event
  $('body').on('kill-all-popovers', function(e) {
    // FIXME: This may be incompatible with bootstrap popover assumptions...
    // This is when the triggering element has been removed from the DOM
    // so we have to kill the popover elements themselves.
    $('.popover').remove();
  });
});

jQuery(function($) {
  // tree

  $('body').on('click', 'ul.tree .item-title', function(e) {
    var $this = $(this),
        $content = $this.closest('li').find('.item-content');

    if($this.hasClass("active")) {
      $content.slideUp('fast');
      $this.removeClass("active");
    } else {
      $content.slideDown('fast');
      $this.addClass("active");
    }

  });


  // tree-structure

  $('body').on('click', 'ul.tree-structure .item-main .grcobject, ul.tree-structure .item-main .openclose', function(e) {
    openclose.call(this);
    e.stopPropagation();
  });

  function openclose(command) {
    var $that = $(this)
    , use_slide = $that.length < 100

    $that.each(function(){
      var $this = $(this)
        , $main = $this.closest('.item-main')
        , $li = $main.closest('li')
        , $content = $li.children('.item-content')
        , $icon = $main.find('.openclose')
        , $parentTree = $this.closest('ul.new-tree')
        , cmd = command
        , callback
        ;

      callback = function() {
        //  Trigger update for sticky headers and footers
        $this.trigger("updateSticky");
      };

      if(typeof cmd !== "string" || cmd === "toggle") {
        cmd = $icon.hasClass("active") ? "close" : "open";
      }

      if (cmd === "close") {
        if (use_slide) {
          $content.slideUp('fast', callback);
        } else {
          $content.css("display", "none");
          callback();
        }
        $icon.removeClass('active');
        $li.removeClass('item-open');
        // Only remove tree open if there are no open siblings
        !$li.siblings('.item-open').length && $parentTree.removeClass('tree-open');
        $content.removeClass('content-open');
      } else if(cmd === "open") {
        if (use_slide) {
          $content.slideDown('fast', callback);
        } else {
          $content.css("display", "block");
          callback();
        }
        $icon.addClass('active');
        $li.addClass('item-open');
        $parentTree.addClass('tree-open');
        $content.addClass('content-open');
      }
    });

    return this;

  }

  $.fn.openclose = openclose;

});

$(window).load(function(){
  // affix setup
  $(window).scroll(function(){
    if($('.header-content').hasClass('affix')) {
      $('.header-content').next('.content').addClass('affixed');
    } else {
      $('.header-content').next('.content').removeClass('affixed');
    }
  });

  // Google Circle CTA Button
  $('body').on('mouseenter', '.square-trigger', function() {
    var $this = $(this),
        $popover = $this.closest('.circle-holder').find('.square-popover');

    $popover.slideDown('fast');
    $this.addClass("active");
    return false;
  });
  $('body').on('mouseleave', '.square-popover', function() {
    var $this = $(this),
        $trigger = $this.closest('.circle-holder').find('.square-trigger');

    $this.slideUp('fast');
    $trigger.removeClass('active');
    $this.removeClass("active");
    return false;
  });

  // References popup preview
  $('body').on('mouseenter', '.new-tree .tree-info a.reference', function() {
    if($(this).width() > $('.new-tree .tree-info').width()) {
      $(this).addClass('shrink-it');
    }
  });

  // Popover trigger for person tooltip in styleguide
  // The popover disappears if the show/hide isn't controlled manually
  var last_popover;
  $('body').on('mouseenter', '.person-tooltip-trigger', function(ev) {
    var target = $(ev.currentTarget),
        content = target.closest('.person-holder').find('.custom-popover-content').html();

    if (!content) {
      // Don't show tooltip if there is no content
      return;
    }
    if (!target.data('popover')) {
      target.popover({
          html: true
        , delay: { show: 400, hide: 200 }
        , trigger: 'manual'
        , content: function() {
            return content;
          }
      });
      target.data('popover').tip().addClass('person-tooltip').css("z-index", 2000);
    }

    var popover = target.data('popover');

    if (last_popover && last_popover !== popover) {
      last_popover.hide();
    }

    // If the popover is active, just refresh the timeout
    if (popover.tip().is(':visible') && popover.timeout) {
      clearTimeout(popover.timeout);
      popover.hoverState = 'in';
    }
    // Otherwise show popover
    else {
      clearTimeout(popover.timeout);
      popover.enter(ev);
    }

    last_popover = popover;
  });
  $('body').on('mouseenter', '.popover', function(ev) {
    // Refresh the popover
    if (last_popover && last_popover.tip().is(':visible')) {
      ev.currentTarget = last_popover.$element[0];
      clearTimeout(last_popover.timeout);
      last_popover.hoverState = 'in';
    }
  });
  $('body').on('mouseleave', '.person-holder, .person-tooltip-trigger, .popover, .popover .square-popover', function(ev) {
    var target = $(ev.currentTarget)
      , popover
      ;

    if (target.is('.person-tooltip-trigger')) {
      target = target.closest('.person-holder');
    }
    else if (target.is('.square-popover')) {
      target = target.closest('.popover');
    }

    // Hide the popover if we left for good
    if (target.is('.person-holder') && (target = target.find('.person-tooltip-trigger')) && (popover = target.data('popover'))) {
      ev.currentTarget = target[0];
      popover.leave(ev);
    }
    // Check if this popover originated from the last person popover
    else if (last_popover && target.is('.popover') && last_popover.tip()[0] === target[0]) {
      ev.currentTarget = last_popover.$element[0];
      last_popover.leave(ev);
    }
  });

  // Tab indexing form fields in modal
  $('body').on('focus', '.modal', function() {
    $('.wysiwyg-area').each(function() {
      var $this = $(this),
          $textarea = $this.find('textarea.wysihtml5').attr('tabindex'),
          $descriptionField = $this.find('iframe.wysihtml5-sandbox');

      function addingTabindex() {
        $descriptionField.attr('tabindex', $textarea);
      }
      setTimeout(addingTabindex,100)
    });
  });

  // Prevent link popup in code mode
  $('body').on('click', 'a[data-wysihtml5-command=popupCreateLink]', function(e){
    var $this = $(this);
    if($this.hasClass('disabled')){
      // The button is disabled, close the modal immediately
      $('body').find('.bootstrap-wysihtml5-insert-link-modal').modal('hide');
      $this.closest('.wysiwyg-area').find('textarea').focus()
    }
  });

  // Watermark trigger
  $('body').on('click', '.watermark-trigger', function() {
    var $this = $(this),
        $showWatermark = $this.closest('.tree-item').find('.watermark-icon');

    $showWatermark.fadeIn('fast');
    $this.addClass("active");
    $this.html('<span class="utility-link"><i class="grcicon-watermark"></i> Watermarked</span>');

    return false;

  });

  // top nav dropdown position
  function dropdownPosition() {
    var $this = $(this),
        $dropdown = $this.closest(".hidden-widgets-list").find(".dropdown-menu"),
        $menu_item = $dropdown.find(".inner-nav-item").find("a"),
        offset = $this.offset(),
        win = $(window),
        win_width = win.width();

    if(win_width - offset.left < 322) {
      $dropdown.addClass("right-pos");
    } else {
      $dropdown.removeClass("right-pos");
    }
    if($menu_item.length === 1) {
      $dropdown.addClass("one-item");
    } else {
      $dropdown.removeClass("one-item");
    }
  }
  $(".dropdown-toggle").on("click", dropdownPosition);

});

jQuery(function($){
  $.fn.cms_wysihtml5 = function() {

    if ($(this).data('_wysihtml5_initialized'))
      return;

    $(this).data('_wysihtml5_initialized', true);
    this.wysihtml5({
        link: true,
        image: false,
        html: true,
        'font-styles': false,
        parserRules: wysihtml5ParserRules });

    this.each(function() {
      var $that = $(this)
      , editor = $that.data("wysihtml5").editor
      , $textarea = $(editor.textarea.element);

      if($that.data("cms_events_bound"))
        return;

      editor.on("change", function(data) {
        $that.html(this.getValue()).trigger("change");
      });

      var $wysiarea = $that.closest(".wysiwyg-area").resizable({
        handles : "s"
        , minHeight : 100
        , alsoResize : "#" + $that.uniqueId().attr("id") + ", #" + $that.closest(".wysiwyg-area").uniqueId().attr("id") + " iframe"
        , autoHide : false
      }).bind("resizestop", function(ev) {
        ev.stopPropagation();
        $that.css({"display" : "block", "height" : $that.height() + 20}); //10px offset between reported height and styled height.
        $textarea.css('width', $textarea.width()+20);
        editor.composer.style();// re-copy new size of textarea to composer
        editor.fire('change_view', editor.currentView.name);
      });
      var $sandbox = $wysiarea.find(".wysihtml5-sandbox");

      $($sandbox.prop("contentWindow"))
      .bind("mouseover mousemove mouseup", function(ev) {
        var e = new $.Event(ev.type === "mouseup" ? "mouseup" : "mousemove"); //jQUI resize listens on this.
        e.pageX = $sandbox.offset().left + ev.pageX;
        e.pageY = $sandbox.offset().top + ev.pageY;
        $sandbox.trigger(e);
      });

      $that.data("cms_events_bound", true);
    });

    return this;
  };

  $(document.body).on("shown", ".bootstrap-wysihtml5-insert-link-modal", function(e) {
    $(this).draggable({ handle : ".modal-header"})
    .find(".modal-header [data-dismiss='modal']").css("opacity", 1);
  });

  $(document.body).on("change", ".rotate_control_assessment", function(ev) {
    ev.currentTarget.click(function() {
      ev.currentTarget.toggle();
    });
  });
});

jQuery(function($){
  var MAX_RESULTS = 20;
  $.widget(
    "ggrc.autocomplete",
    $.ui.autocomplete,
    {
      options: {
        // Ensure that the input.change event still occurs
        change: function(event, ui) {
          if(!$(event.target).parents(document.body).length)
            console.warn("autocomplete menu change event is coming from detached nodes");
          $(event.target).trigger("change");
        },

        minLength: 0,

        source: function(request, response) {
          // Search for the people based on the term
          var query = request.term || '',
              queue = new RefreshQueue(),
              that = this,
              is_next_page = request.start != null,
              dfd;

          if (query.indexOf('@') > -1)
            query = '"' + query + '"';

          this.last_request = request;
          if(is_next_page) {
            dfd = $.when(this.last_stubs);
          } else {
            request.start = 0;
            dfd = this.options.source_for_refreshable_objects.call(this, request);
          }

          this.options.controller.bindXHRToButton(
            // Retrieve full people data

          dfd.then(function(objects) {
            that.last_stubs = objects;
            can.each(objects.slice(request.start, request.start + MAX_RESULTS), function(object) {
              queue.enqueue(object);
            });
            queue.trigger().then(function(objs) {
              objs = that.options.apply_filter.call(that, objs, request);
              if(objs.length || is_next_page) {
                // Envelope the object to not break model instance due to
                // shallow copy done by jQuery in `response()`
                objs = can.map(objs, function(obj) { return { item: obj }; });
                response(objs);
              } else {
                // show the no-results option iff no results come through here,
                //  and not merely showing paging.
                that._suggest( [] );
                that._trigger( "open" );
              }
            });
          }), $(this.element), null, false);
        },

        apply_filter: function(objects) {
          return objects;
        },

        source_for_refreshable_objects: function(request) {
          var that = this;

          if (this.options.searchlist) {
            return this.options.searchlist.then(function() {
              var filtered_list = [];
              return $.map(arguments, function(item) {
                if (!item) {
                  return;
                }
                var search_attr = item.title || "",
                    term = request.term.toLowerCase();

                // Filter out duplicates:
                if (filtered_list.indexOf(item._cid) > -1) {
                  return;
                }
                filtered_list.push(item._cid);

                // Perform search based on term:
                if (search_attr.toLowerCase().indexOf(term) === -1) {
                  return;
                }
                return item;
              });
            });
          }

          return GGRC.Models.Search
            .search_for_types(
              request.term || '',
              this.options.searchtypes,
              {
              // FIXME: Remove or figure out when this is necessary.
              //{
              //  __permission_type: 'create'
              //  , __permission_model: 'Object' + $that.data("lookup")
              })
            .then(function(search_result) {
              var objects = [];

              can.each(that.options.searchtypes, function(searchtype) {
                objects.push.apply(
                  objects, search_result.getResultsForType(searchtype));
              });
              return objects;
            });
        },

        select: function(ev, ui) {
          var original_event,
              that = this,
              ctl = $(this).data($(this).data("autocomplete-widget-name")).options.controller
              ;

          if(ui.item) {
            return ctl.autocomplete_select($(this), ev, ui);
          } else {
            original_event = event;
            $(document.body).off(".autocomplete").one("modal:success.autocomplete", function(_ev, new_obj) {
              ctl.autocomplete_select($(that), original_event, { item : new_obj });
              $(that).trigger("modal:success", new_obj);
            }).one("hidden", function() {
              setTimeout(function() {
                $(this).off(".autocomplete");
              }, 100);
            });
            while(original_event = original_event.originalEvent) {
              if(original_event.type === "keydown") {
                //This selection event was generated from a keydown, so click the add new link.
                var widget_name = el.data("autocompleteWidgetName");
                el.data(widget_name).menu.active.find("a").click();
                break;
              }
            }
            return false;
          }
        },

        close: function() {
          delete this.scroll_op_in_progress;
          //$that.val($that.attr("value"));
        }
      },

      _create: function() {
        var that = this,
            $that = $(this.element),
            base_search = $that.data("lookup"),
            from_list = $that.data("from-list"),
            searchtypes;

        this._super.apply(this, arguments);

        $that.data("autocomplete-widget-name", this.widgetFullName);

        $that.focus(function() {
          $(this).data(that.widgetFullName).search($(this).val());
        });

        if (from_list) {
          this.options.searchlist = $.when.apply(this, $.map(from_list.list, function(item) {
            var props = base_search.trim().split('.');
            return item.instance.refresh_all.apply(item.instance, props);
          }));
        } else if (base_search) {
          base_search = base_search.trim();
          if (base_search.indexOf("__mappable") === 0 || base_search.indexOf("__all") === 0) {
            searchtypes = GGRC.Mappings.get_canonical_mappings_for(
              this.options.parent_instance.constructor.shortName
              );
            if (base_search.indexOf("__mappable") === 0) {
              searchtypes = can.map(searchtypes, function(mapping) {
                return mapping instanceof GGRC.ListLoaders.ProxyListLoader ? mapping : undefined;
              });
            }
            if (base_search.indexOf("_except:")) {
              can.each(base_search.substr(base_search.indexOf("_except:") + 8).split(","), function(remove) {
                delete searchtypes[remove];
              });
            }
            searchtypes = Object.keys(searchtypes);
          } else {
            searchtypes = base_search.split(",");
          }

          this.options.searchtypes = can.map(searchtypes, function(t) {
            return CMS.Models[t].model_singular;
          });
        }
      },

      _setup_menu_context : function(items) {
          var model_class = this.element.data("lookup")

            , model = CMS.Models[model_class || this.element.data("model")]
                      || GGRC.Models[model_class || this.element.data("model")]
            ;

          return {
            model_class: model_class,
            model : model,
            // Reverse the enveloping we did 25 lines up
            items: can.map(items, function(item) { return item.item; }),
          };
      },

      _renderMenu: function(ul, items) {
        var template = this.element.data("template"),
          context = new can.Observe(this._setup_menu_context(items)),
          model = context.model,
          that = this,
          $ul = $(ul)
          ;

        if (!template) {
          if(model && GGRC.Templates[model.table_plural + "/autocomplete_result"]) {
            template = '/' + model.table_plural + '/autocomplete_result.mustache';
          } else {
            template = '/base_objects/autocomplete_result.mustache';
          }
        }

        $ul.unbind("scrollNext")
        .bind("scrollNext", function(ev, data) {
          if(that.scroll_op_in_progress) {
            return;
          }
          that.scroll_op_in_progress = true;
          that.last_request = that.last_request || {};
          that.last_request.start = that.last_request.start || 0;
          that.last_request.start += MAX_RESULTS;
          context.attr("items_loading", true);
          that.source(that.last_request, function(items) {
            context.items.push.apply(context.items, can.map(items, function(item) { return item.item; }));
            context.removeAttr("items_loading");
            setTimeout(function() {
              delete that.scroll_op_in_progress;
            }, 10);
          });
        });

        can.view.render(
          GGRC.mustache_path + template,
          context,
          function(frag) {
            $ul.html(frag);
            $ul.cms_controllers_lhn_tooltips().cms_controllers_infinite_scroll();
            can.view.hookup(ul);
          });
      }
  });
  $.widget.bridge("ggrc_autocomplete", $.ggrc.autocomplete);

  $.widget("ggrc.mapping_autocomplete", $.ggrc.autocomplete, {
    options: {
      source_for_refreshable_objects: function(request) {
        var $el = $(this.element),
          mapping = this.options.controller.options;

        if (mapping.scope) {
          mapping = mapping.scope.source_mapping;
        } else {
          mapping = inst.source_mapping;
        }

        return $.when(can.map(mapping, function(binding) {
          return binding.instance;
        }));
      },
      apply_filter: function(objects, request) {
        return can.map(objects, function(object) {
          if (!request.term || object.title && ~object.title.indexOf(request.term))
            return object;
          else
            return undefined;
        });
      }
    },
      _setup_menu_context : function(items) {
        return $.extend(this._super(items), {
          mapping : this.options.mapping == null ? this.element.data("mapping") : this.options.mapping
        });
      }
  });
  $.widget.bridge("ggrc_mapping_autocomplete", $.ggrc.mapping_autocomplete);

  $.cms_autocomplete = function(el) {
    var ctl = this;
    // Add autocomplete to the owner field
    ($(el) || this.element.find('input[data-lookup]'))
    .filter("[name][name!='']")
    .ggrc_autocomplete({ controller: ctl });
  };

});

jQuery(function($) {
  // Trigger compilation of any remaining preloaded Mustache templates for
  // faster can.view() response time.

  setTimeout(function() {

    GGRC.queue_event(
      can.map(GGRC.Templates, function(template, id) {
        var key = can.view.toId(GGRC.mustache_path + "/" + id + ".mustache");
        if(!can.view.cachedRenderers[key]) {
          return function() {
            can.view.mustache(key, template);
          };
        }
      })
    );
  }, 2000);

});

(function($) {

  window.getPageToken = function getPageToken() {
      return $(document.body).data("page-subtype")
            || $(document.body).data("page-type")
            || window.location.pathname.substring(1, (window.location.pathname + "/").indexOf("/", 1));
    }

// a few core CanJS extensions below.

// Core validation for fields not being "blank", i.e.
//  having no content when outside spaces are trimmed away.
can.Model.validationMessages.non_blank = can.Map.validationMessages.non_blank = "cannot be blank";

can.Model.validateNonBlank = can.Map.validateNonBlank = function(attrNames, options) {
    can.Map.validate.call(this, attrNames, options, function(value) {
        if (typeof value === 'undefined' || value === null || typeof value.trim === "function" && value.trim() === '') {
            return this.constructor.validationMessages.non_blank;
        }
    });
};

// Adding reduce, a generally useful array comprehension.
//  Bitovi decided against including it in core CanJS, but
//  adding it here for easy universal use across can.List
//  as well as arrays.
can.reduce ||
  (can.reduce = function(a, f, i) { if(a==null) return null; return [].reduce.apply(a, arguments.length < 3 ? [f] : [f, i]) });
})(window.jQuery);
