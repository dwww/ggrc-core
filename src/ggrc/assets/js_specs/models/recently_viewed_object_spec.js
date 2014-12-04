/*!
    Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
    Created By: silas@reciprocitylabs.com
    Maintained By: brad@reciprocitylabs.com
*/

//= require models/local_storage

describe("can.Model.RecentlyViewedObjects", function() {

  describe("::newInstance", function() {
    it("creates a new recently viewed object given non-Model instance", function() {
      var obj = GGRC.Models.RecentlyViewedObject.newInstance({"foo": "bar"});
      expect(obj.foo).toBe("bar");
      expect(obj instanceof GGRC.Models.RecentlyViewedObject).toBeTruthy();
    });

    it("references original Model type when passed in as argument", function() {
      spyOn(GGRC.Models.RecentlyViewedObject.prototype, "init");
      can.Model("RVO");
      var obj = new RVO({
          viewLink: "/"
          , title: "blah"
      });
      var rvo_obj = GGRC.Models.RecentlyViewedObject.newInstance(obj);
      expect(rvo_obj.type).toBe("RVO");
      expect(rvo_obj.model).toBe(RVO);
      expect(rvo_obj.viewLink).toBe("/");
      expect(rvo_obj.title).toBe("blah");
    });
  });

  describe("#stub", function() {
    it("include title and view link", function() {
      var obj = {
          viewLink: "/"
          , title: "blah"
      };
      var rvo_obj = new GGRC.Models.RecentlyViewedObject(obj).stub();
      expect(rvo_obj.title).toBe("blah");
      expect(rvo_obj.viewLink).toBe("/");
      expect(rvo_obj.id).not.toBeDefined();
    });
  });
});
