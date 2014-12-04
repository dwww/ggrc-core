/*!
    Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
    Created By: vraj@reciprocitylabs.com
    Maintained By: vraj@reciprocitylabs.com
*/

(function(can, $) {

GGRC.Controllers.Modals("GGRC.Controllers.Unmap", {
    defaults: {
        skip_refresh: true
    }
}, {
  init : function() {
    this._super();
  }

  , "{$footer} a.btn[data-toggle=delete] click" : function(el, ev) {
    this.element.trigger("modal:success", this.options.instance);
  }

});

})(window.can, window.can.$);
