/*!
    Copyright (C) 2013 Google Inc., authors, and contributors <see AUTHORS file>
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
    Created By: brad@reciprocitylabs.com
    Maintained By: brad@reciprocitylabs.com
*/

;(function(can) {

can.Model.Cacheable("CMS.Models.Audit", {
  root_object : "audit"
  , root_collection : "audits"
  , category : "programs"
  , findOne : "GET /api/audits/{id}"
  , update : "PUT /api/audits/{id}"
  , destroy : "DELETE /api/audits/{id}"
  , create : "POST /api/audits"
  , mixins : ["contactable", "unique_title"]
  , attributes : {
      context : "CMS.Models.Context.stub"
    , program: "CMS.Models.Program.stub"
    , requests : "CMS.Models.Request.stubs"
    , modified_by : "CMS.Models.Person.stub"
    , start_date : "date"
    , end_date : "date"
    , report_start_date : "date"
    , report_end_date : "date"
    , object_people : "CMS.Models.ObjectPerson.stubs"
    , people : "CMS.Models.Person.stubs"
    , contact : "CMS.Models.Person.stub"
    , audit_firm : "CMS.Models.OrgGroup.stub"
    , audit_objects : "CMS.Models.AuditObject.stubs"
  }
  , defaults : {
    status : "Draft",
    object_type: "Control"
  }
  , tree_view_options : {
    draw_children : true
    , child_options : [{
      model : "Request"
      , mapping: "requests"
      , allow_creating : true
      , parent_find_param : "audit.id"
    },
    {
      model : "Request"
      , mapping: "related_owned_requests"
      , allow_creating : true
      , parent_find_param : "audit.id"
    },
    {
      model : "Response"
      , mapping: "related_owned_responses"
      , allow_creating : false
      , parent_find_param : "audit.id"
    },
    {
      model : "Request"
      , mapping: "related_mapped_requests"
      , allow_creating : false
      , parent_find_param : "audit.id"
    },
    {
      model : "Response"
      , mapping: "related_mapped_responses"
      , allow_creating : false
      , parent_find_param : "audit.id"
    }]
  }
  , init : function() {
    this._super && this._super.apply(this, arguments);
    this.validatePresenceOf("program");
    this.validatePresenceOf("contact");
    this.validateNonBlank("title");
    this.validate(["_transient.audit_firm", "audit_firm"], function(newVal, prop) {
      var audit_firm = this.attr("audit_firm");
      var audit_firm_text = this.attr("_transient.audit_firm");
      if(!audit_firm && audit_firm_text
        || (audit_firm_text !== "" && audit_firm_text != null && audit_firm != null && audit_firm_text !== audit_firm.reify().title)) {
        return "No valid org group selected for firm";
      }
    });
    // Preload auditor role:
    CMS.Models.Role.findAll({name__in: "Auditor"});
  }
}, {
  object_model: can.compute(function() {
    return CMS.Models[this.attr("object_type")];
  }),
  save : function() {

    var that = this;
    // Make sure the context is always set to the parent program
    if(this.context == null || this.context.id == null){
      this.attr('context', this.program.reify().context);
    }

    return this._super.apply(this, arguments).then(function(instance) {
      // Since Audits have a non-standard url for viewing, the url has to be set here
      // so that the browser can be redirected properly after creating.
      instance.attr('_redirect',
        instance.program.reify().viewLink + "#audit_widget/audit/" + instance.id);
      return instance;
    });
  },
  findAuditors : function(return_list){
    // If return_list is true, use findAuditors in the
    //  classical way, where the exact state of the list
    //  isn't needed immeidately (as in a Mustache helper);
    //  if false, return a deferred that resolves to the list
    //  when the list is fully ready, for cases like permission
    //  checks for other modules.
    var loader = this.get_binding('authorizations'),
      auditors_list = new can.List(),
      dfds = []
      ;

    if(return_list) {
      $.map(loader.list, function(binding) {
        // FIXME: This works for now, but is sad.
        if (!binding.instance.selfLink)
          return;
        var role = binding.instance.role.reify();
        function checkRole() {
          if (role.attr('name') === 'Auditor') {
            auditors_list.push({
              person: binding.instance.person.reify()
              , binding: binding.instance
            });
          }
        }
        if(role.selfLink) {
          checkRole();
        } else {
          role.refresh().then(checkRole);
        }
      });
      return auditors_list;
    } else {
      return loader.refresh_instances().then(function() {
        $.map(loader.list, function(binding) {
          // FIXME: This works for now, but is sad.

          dfds.push(new $.Deferred(function(dfd) {

            if (!binding.instance.selfLink) {
              binding.instance.refresh().then(function() {
                dfd.resolve(binding.instance);
              });
            } else {
              dfd.resolve(binding.instance);
            }
          }).then(function(instance) {

            var role = instance.role.reify();
            function checkRole() {
              if (role.attr('name') === 'Auditor') {
                auditors_list.push({
                  person: instance.person.reify()
                  , binding: instance
                });
              }
            }
            if(role.selfLink) {
              checkRole();
            } else {
              return role.refresh().then(checkRole);
            }
          }));
        });
        return $.when.apply($, dfds).then(function() {
          return auditors_list;
        });
      });
    }
  }
});

can.Model.Mixin("requestorable", {
  before_create : function() {
    if(!this.requestor) {
      this.attr('requestor', { id: GGRC.current_user.id, type : "Person" });
    }
  }
  , form_preload : function(new_object_form) {
    if(new_object_form) {
      if(!this.requestor) {
        this.attr('requestor', { id: GGRC.current_user.id, type : "Person" });
      }
    }
  }
});

can.Model.Cacheable("CMS.Models.Request", {
  root_object : "request"
  , root_collection : "requests"
  , create : "POST /api/requests"
  , update : "PUT /api/requests/{id}"
  , destroy : "DELETE /api/requests/{id}"
  , mixins : ["unique_title", "requestorable"]
  , attributes : {
      context : "CMS.Models.Context.stub"
    , audit : "CMS.Models.Audit.stub"
    , responses : "CMS.Models.Response.stubs"
    , assignee : "CMS.Models.Person.stub"
    , requestor : "CMS.Models.Person.stub"
    , audit_object : "CMS.Models.AuditObject.stub"
    , requested_on : "date"
    , due_on : "date"
  }
  , defaults : {
    status : "Draft"
    , requested_on : new Date()
    , due_on : null
  }
  , tree_view_options : {
    show_view : GGRC.mustache_path + "/requests/tree.mustache"
    , header_view : GGRC.mustache_path + "/requests/filters.mustache"
    , footer_view : GGRC.mustache_path + "/requests/tree_footer.mustache"
    , draw_children : true
    , child_options : [{
      model : "Response"
      , mapping : "responses"
      , allow_creating : true
    }]
  }
  , init : function() {
    this._super.apply(this, arguments);
    this.validateNonBlank("description");
    this.validateNonBlank("due_on");
    this.validatePresenceOf("assignee");
    if(this === CMS.Models.Request) {
      this.bind("created", function(ev, instance) {
        if(instance.constructor === CMS.Models.Request) {
          instance.audit.reify().refresh();
        }
      });
    }
  }
}, {
  init : function() {
    this._super && this._super.apply(this, arguments);
    function setAssigneeFromAudit() {
      if(!this.selfLink && !this.assignee && this.audit) {
        this.attr("assignee", this.audit.reify().contact || {id : null});
      }
    }
    setAssigneeFromAudit.call(this);

    this.bind("audit", setAssigneeFromAudit);
    this.attr("response_model_class", can.compute(function() {
      return can.capitalize(this.attr("request_type")
          .replace(/ [a-z]/g, function(a) { return a.slice(1).toUpperCase(); }))
        + "Response";
    }, this));
  }

  , display_name : function() {
      var desc = this.description
        , max_len = 20;
      out_name = desc;
      // Truncate if greater than max_len chars
      if (desc.length > max_len) {
        out_name = desc.slice(0, max_len) + " ...";
      }
      return 'Request "' + out_name + '"';
    }
  , before_create : function() {
    var audit, that = this;
    if(!this.assignee) {
      audit = this.audit.reify();
      (audit.selfLink ? $.when(audit) : audit.refresh())
      .then(function(audit) {
        that.attr('assignee', audit.contact);
      });
    }
  }
  , after_save: function() {
    var that = this;
    
    new RefreshQueue().enqueue(this.audit.reify()).trigger().then(function(audits) {
      return new RefreshQueue().enqueue(audits[0].program).trigger();
    }).then(function(programs) {
      return $.when(
        programs[0],
        programs[0].get_binding("authorized_people").refresh_instances(),
        CMS.Models.Role.findAll({ name : "ProgramReader" }));
    }).then(function(program, people_bindings, reader_roles) {
      if(Permission.is_allowed("create", "UserRole", program.context)
        && !~can.inArray(
          that.assignee.reify(),
          can.map(people_bindings, function(pb) { return pb.instance; })
      )) {
        new CMS.Models.UserRole({
          person: that.assignee,
          role: reader_roles[0].stub(),
          context: program.context
        }).save();
      }
    });
  },
  before_save: function(notifier) {
    var that = this,
        obj = this.audit_object_object ? this.audit_object_object.reify() : this.audit_object_object,
        matching_objs;
    if(that.audit_object
       && (!that.audit_object_object
           || that.audit_object.reify().auditable.id !== that.audit_object_object.id
    )) {
      return;
    }
    if(obj && (matching_objs = can.map(this.get_mapping("audit_objects_via_audit"), function(mapping) {
      if(mapping.instance === obj)
        return mapping;
    })).length < 1) {
      notifier.queue(
        new CMS.Models.AuditObject({
          audit: this.audit,
          auditable: this.audit_object_object,
          context: this.audit.reify().context
        }).save().then(function(ao) {
          that.attr("audit_object", ao.stub());
        })
      );
    } else {
      that.attr("audit_object", matching_objs && matching_objs.length && matching_objs[0].mappings[0].instance.stub() || null);
    }
  }
  , form_preload : function(new_object_form) {
    var audit, that = this;
    if(new_object_form) {
      if(!this.assignee && this.audit) {
        audit = this.audit.reify();
        (audit.selfLink ? $.when(audit) : audit.refresh())
        .then(function(audit) {
          that.attr('assignee', audit.contact);
        });
      }
    }
  }

});


can.Model.Cacheable("CMS.Models.Response", {

  root_object : "response"
  , root_collection : "responses"
  , subclasses : []
  , init : function() {
    this._super && this._super.apply(this, arguments);

    function refresh_request(ev, instance) {
      if(instance instanceof CMS.Models.Response) {
        instance.request.reify().refresh();
      }
    }
    this.cache = {};
    if(this !== CMS.Models.Response) {
      CMS.Models.Response.subclasses.push(this);
    } else {
      this.bind("created", refresh_request);
      this.bind("destroyed", refresh_request);
    }
  }
  , create : "POST /api/responses"
  , update : "PUT /api/responses/{id}"

  , findAll : "GET /api/responses"
  , findOne : "GET /api/responses/{id}"
  , destroy : "DELETE /api/responses/{id}"
  , model : function(params) {
    var found = false;
    if (this.shortName !== 'Response')
      return this._super(params);
    if (!params 
        || (params instanceof CMS.Models.Response 
            && params.constructor !== CMS.Models.Response
       ))
      return params;
    params = this.object_from_resource(params);
    if (!params.selfLink) {
      if (params.type && params.type !== 'Response')
        return CMS.Models[params.type].model(params);
    } else {
      can.each(this.subclasses, function(m) {
        if(m.root_object === params.response_type + "_response") {
          params = m.model(params);
          found = true;
          return false;
        } else if(m.root_object in params) {
          params = m.model(m.object_from_resource(params));
          found = true;
          return false;
        }
      });
    }
    if(found) {
      return params;
    } else {
      console.debug("Invalid Response:", params);
    }
  }

  , attributes : {
      context : "CMS.Models.Context.stub"
    , object_documents : "CMS.Models.ObjectDocument.stubs"
    , documents : "CMS.Models.Document.stubs"
    , population_worksheet : "CMS.Models.Document.stub"
    , sample_worksheet : "CMS.Models.Document.stub"
    , sample_evidence : "CMS.Models.Document.stub"
    , object_people : "CMS.Models.ObjectPerson.stubs"
    , people : "CMS.Models.Person.stubs"
    , meetings : "CMS.Models.Meeting.stubs"
    , request : "CMS.Models.Request.stub"
    , assignee : "CMS.Models.Person.stub"
    , related_sources : "CMS.Models.Relationship.stubs"
    , related_destinations : "CMS.Models.Relationship.stubs"
    , object_controls : "CMS.Models.ObjectControl.stubs"
    , controls : "CMS.Models.Control.stubs"
    , contact : "CMS.Models.Person.stub"
  }
  , defaults : {
    status : "Assigned"
  }
  , tree_view_options : {
    show_view : GGRC.mustache_path + "/responses/tree.mustache"
    , footer_view : GGRC.mustache_path + "/responses/tree_footer.mustache"
    , draw_children : true
    , child_options : [{
      //0: mapped objects
      mapping : "business_objects"
      , model : can.Model.Cacheable
      , show_view : GGRC.mustache_path + "/base_objects/tree.mustache"
      , footer_view : GGRC.mustache_path + "/base_objects/tree_footer.mustache"
      , allow_mapping : false
      , allow_creating: false
      , exclude_option_types : function() {
        var types = {
          "DocumentationResponse" : "Document"
          , "InterviewResponse" : "Person"
        };
        return types[this.parent_instance.constructor.shortName] || "";
      }
    }, {
      //1: Document Evidence
      model : "Document"
      , mapping : "documents"
      , show_view : GGRC.mustache_path + "/documents/pbc_tree.mustache"
      , allow_mapping: false
      , allow_creating: false
    }, {
      //3: Meeting participants
      model : "Person"
      , mapping : "people"
      , show_view : GGRC.mustache_path + "/people/tree.mustache"
      , footer_view : GGRC.mustache_path + "/people/tree_footer.mustache"
      , allow_mapping: false
      , allow_creating: false
    }, {
      //2: Meetings
      model : "Meeting"
      , mapping : "meetings"
      , show_view : GGRC.mustache_path + "/meetings/tree.mustache"
      , footer_view : GGRC.mustache_path + "/meetings/tree_footer.mustache"
      , allow_mapping: false
      , allow_creating: false
    }]
  }
}, {
    display_name : function() {
      var desc = this.description
        , max_len = 20;
      out_name = desc;
      // Truncate if greater than max_len chars
      if (desc.length > max_len) {
        out_name = desc.slice(0, max_len) + " ...";
      }
      return 'Response "' + out_name + '"';
    }
  , before_create : function() {
    if(!this.contact) {
      this.attr("contact", this.request.reify().assignee);
    }
  }
  , preload_form : function(new_object_form) {
    if(new_object_form && !this.contact) {
      this.attr("contact", this.request.reify().assignee);
    }
  }

});

CMS.Models.Response("CMS.Models.DocumentationResponse", {
  root_object : "documentation_response"
  , root_collection : "documentation_responses"
  , create : "POST /api/documentation_responses"
  , update : "PUT /api/documentation_responses/{id}"
  , findAll : "GET /api/documentation_responses"
  , findOne : "GET /api/documentation_responses/{id}"
  , destroy : "DELETE /api/documentation_responses/{id}"
  , attributes : {}
  , init : function() {
    this._super && this._super.apply(this, arguments);
    can.extend(this.attributes, CMS.Models.Response.attributes);
    this.cache = CMS.Models.Response.cache;
  }
  , process_args : function(args, names) {
    var params = this._super(args, names);
    params[this.root_object].response_type = "documentation";
    return params;
  }
}, {});

CMS.Models.Response("CMS.Models.InterviewResponse", {
  root_object : "interview_response"
  , root_collection : "interview_responses"
  , create : "POST /api/interview_responses"
  , update : "PUT /api/interview_responses/{id}"
  , findAll : "GET /api/interview_responses"
  , findOne : "GET /api/interview_responses/{id}"
  , destroy : "DELETE /api/interview_responses/{id}"
  , attributes : {}
  , init : function() {
    this._super && this._super.apply(this, arguments);
    can.extend(this.attributes, CMS.Models.Response.attributes);
    this.cache = CMS.Models.Response.cache;
  }
  , process_args : function(args, names) {
    var params = this._super(args, names);
    params[this.root_object].response_type = "interview";
    return params;
  }
}, {
  save : function() {
    var that = this;
    if(this.isNew()) {
      var audit = this.request.reify().audit.reify()
        , auditors_dfd = audit.findAuditors();

      return auditors_dfd.then(function(auditors) {
        if(auditors.length > 0){
          that.mark_for_addition("people", auditors[0].person);
        }
        that.mark_for_addition("people", that.contact);
        return that._super.apply(that, arguments);
      });
    } else {
      return this._super.apply(this, arguments);
    }
  }
});

CMS.Models.Response("CMS.Models.PopulationSampleResponse", {
  root_object : "population_sample_response"
  , root_collection : "population_sample_responses"
  , create : "POST /api/population_sample_responses"
  , update : "PUT /api/population_sample_responses/{id}"
  , findAll : "GET /api/population_sample_responses"
  , findOne : "GET /api/population_sample_responses/{id}"
  , destroy : "DELETE /api/population_sample_responses/{id}"
  , attributes : {}
  , init : function() {
    this._super && this._super.apply(this, arguments);
    can.extend(this.attributes, CMS.Models.Response.attributes);
    this.cache = CMS.Models.Response.cache;
  }
  , process_args : function(args, names) {
    var params = this._super(args, names);
    params[this.root_object].response_type = "population sample";
    return params;
  }
}, {});

can.Model.Cacheable("CMS.Models.Meeting", {
  root_collection : "meetings"
  , root_object : "meeting"
  , findAll : "GET /api/meetings"
  , create : "POST /api/meetings"
  , update : "PUT /api/meetings/{id}"
  , destroy : "DELETE /api/meetings/{id}"
  , attributes : {
      context : "CMS.Models.Context.stub"
    , response : "CMS.Models.Response.stub"
    , people : "CMS.Models.Person.stubs"
    , object_people : "CMS.Models.ObjectPerson.stubs"
    , start_at : "datetime"
    , end_at : "datetime"
  }
  , defaults : {}
  , init : function() {
    this._super && this._super.apply(this, arguments);
    this.validateNonBlank("title");
    this.validateNonBlank("start_at");
    this.validateNonBlank("end_at");
  }
}, {
  init : function () {
      var that = this;
      this._super && this._super.apply(this, arguments);

      this.each(function(value, name) {
        if (value === null)
          that.removeAttr(name);
      });
        that.bind("change", function(){
          if(typeof that.response !== "undefined" && !that._preloaded_people){
            that._preloaded_people = true;

            can.map(that.response.reify().people, function(person){
              that.mark_for_addition("people", person);
            });
          }
        });
  }

});

})(this.can);
