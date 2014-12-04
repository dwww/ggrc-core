/*!
    Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
    Created By: brad@reciprocitylabs.com
    Maintained By: brad@reciprocitylabs.com
*/

(function(can, $) {

can.Control("GGRC.Controllers.RecentlyViewed", {
  defaults : {
    list_view : GGRC.mustache_path + "/dashboard/recently_viewed_list.mustache"
    , max_history : 10
    , max_display : 3
  }
}, {
  init : function() {
    var page_model = GGRC.page_instance();
    var instance_list = [];
    var that = this;

    GGRC.Models.RecentlyViewedObject.findAll().done(function(objs) {
      var max_history = that.options.max_history;
      if(page_model) {
        instance_list.push(new GGRC.Models.RecentlyViewedObject(page_model));
        instance_list[0].save();
        max_history--;
      }

      for(var i = objs.length - 1; i >= 0; i--) {
        if((page_model && page_model.viewLink === objs[i].viewLink)
          || objs.length - i > max_history || !("viewLink" in objs[i])
          ) {
          objs.splice(i, 1)[0].destroy(); //remove duplicate of current page object or excessive objects
        } else if(instance_list.length < that.options.max_display) {
          instance_list.push(objs[i]);
        }
      }

      can.view(that.options.list_view, {list : instance_list}, function(frag) {
        that.element.find(".top-level").html(frag);
      });
    });
  }
});

})(this.can, this.can.$);
