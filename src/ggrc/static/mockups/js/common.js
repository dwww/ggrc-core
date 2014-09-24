$(document).ready(function(){

  $('[rel=tooltip]').tooltip();

  $('.lhs-holder').css('height', $(window).height() - 71 );
  $('.inner-nav').css('height', $(window).height() - 126 );
  $('.object-area').css('height', $(window).height() - 156 );
  $('.object-area').css('width', $(window).width() - 448 );

  $('input[name=notify-digest]').parent().on('click', function(ev){
    ev.stopPropagation();
  });

  $('body').on('click', '.info-expand a', function() {
    var $this = $(this),
        $show_hide = $this.closest('.row-fluid').next('.hidden-fields-area');

    if($this.hasClass("active")) {
      $show_hide.slideUp('fast');
      $this.removeClass("active");
    } else {
      $show_hide.slideDown('fast');
      $this.addClass("active");
    }

    return false;

  });

  $('body').on('click', '.expand-link a', function() {
    var $this = $(this),
        $show_hide = $this.closest('.row-fluid').next('.hidden-fields-area');

    if($this.hasClass("active")) {
      $show_hide.slideUp('fast');
      $this.removeClass("active");
    } else {
      $show_hide.slideDown('fast');
      $this.addClass("active");
    }

    return false;

  });

  $('body').on('click', 'ul.tree-structure .item-main .grcobject, ul.tree-structure .item-main .openclose', function(e) {
    openclose.call(this);
    e.stopPropagation();
  });
  $.fn.openclose = openclose;
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
        , cmd = command;

      if(typeof cmd !== "string" || cmd === "toggle") {
        cmd = $icon.hasClass("active") ? "close" : "open";
      }

      if (cmd === "close") {

        use_slide ? $content.slideUp('fast') : $content.css("display", "none");
        $icon.removeClass('active');
        $li.removeClass('item-open');
        // Only remove tree open if there are no open siblings
        !$li.siblings('.item-open').length && $parentTree.removeClass('tree-open');
        $content.removeClass('content-open');
      } else if(cmd === "open") {
        use_slide ? $content.slideDown('fast') : $content.css("display", "block");
        $icon.addClass('active');
        $li.addClass('item-open');
        $parentTree.addClass('tree-open');
        $content.addClass('content-open');
      }
    });

    return this;

  }

  $.fn.openclose = openclose;

  $('body').on('click', '.advanced-filter-trigger', function() {
    var $this = $(this),
        $filters = $this.closest('.inner-tree').find('.advanced-filters');

    if($this.hasClass("active")) {
      $filters.slideUp('fast');
      $this.removeClass("active");
      $this.html('<i class="grcicon-search"></i> Show Filters');
    } else {
      $filters.slideDown('fast');
      $this.addClass("active");
      $this.html('<i class="grcicon-search"></i> Hide Filters');
    }

    return false;

  });

  $('.autogenerate').change(function(){
    $('.autogenerate-result').toggleClass('active', $(this).val() == 'control');
  });

  $('body').on('click', '.accordion-group > a', function() {
    var $this = $(this),
        $subNav = $this.closest('.accordion-group').find('.sub-level'),
        $subAction = $this.closest('.accordion-group').find('.sub-actions');

    if($this.hasClass("active")) {
      $subNav.slideUp('fast');
      $subAction.slideUp('fast');
      $this.removeClass("active");
    } else {
      $subNav.slideDown('fast');
      $subAction.slideDown('fast');
      $this.addClass("active");
    }

    return false;

  });

  $('body').on('click', '.accordion-group-inner > .arrow', function() {
    var $this = $(this),
        $subNav = $this.closest('.accordion-group-inner').find('.sub-level');

    if($this.hasClass("active")) {
      $subNav.slideUp('fast');
      $this.removeClass("active");
    } else {
      $subNav.slideDown('fast');
      $this.addClass("active");
    }

    return false;

  });

  $( ".date" ).datepicker();

  $(function() {
    var people = [
      "Vladan Mitevski",
      "Predrag Kanazir",
      "Dan Ring",
      "Silas Barta",
      "Cassius Clay"
    ];
    var program = [
      "Google Fiber",
      "LEED",
      "ISO 27001 Program",
      "CFR 21 Part 11",
      "HIPAA",
      "HR Program",
      "SOX Compliance Program",
      "Contract Compliance",
      "PCI Compliance Program",
    ]
    var object = [
      "Stability and Perpetuability"
    ]

    var object2 = [
      "CTRL - Access Control",
      "CTRL - Non Critical Security",
      "POL - User Policy",
      "POL - Universal Policy"
    ]

    var tasks = [
      "Proof Reading",
      "Validate Mappings",
      "Peer Review"
    ]
  });

  // New Assessment Created
  $('body').on('click', '#addAssessmentCreated', function() {
    $('#newAssessment').modal('hide');
    $('#assessmentCountObjectNav').html('2');
    $('#assessmentCountWidget').html('(2)');
    $('#mainAssessmentsCountNew').html('2');
    $('#addAssessment').fadeIn();
    $('#mainAssessmentNew').fadeIn();

  });

  // New Object under Assessment Created
  $('body').on('click', '#addObjectUnderAssessmentCreated', function() {
    $('#newObjectToAssessment').modal('hide');
    $('#objectUnderAssessmentCountObjectNav').html('5');
    $('#objectItemUnderAssessmentCountObjectNav').html('5');
    $('#addObjectUnderAssessment').fadeIn();
  });

  // Create New Task
  $('body').on('click', '#createNewTask', function() {
    $('#newTask').modal('hide');
    $('#newlyCreatedTaskTitle').html('Clean up');
    $('#newlyCreatedTask').fadeIn();
    $('#taskCounter').html('1');
  });

  // Create New File
  $('body').on('click', '#createNewFile', function() {
    $('#newFile').modal('hide');
    $('#newlyCreatedFile').fadeIn();
    $('#fileCounter').html('3');
  });

  $('body').on('click', '.show-long', function() {
    var $this = $(this),
        $description = $this.closest('.show-description').find('.tree-description');

    $this.hide();
    $description.removeClass('short');

    return false;
  });

  $('.workflow-accordion').on('show', function (e) {
    $(e.target).prev('.accordion-heading').find('.accordion-toggle').addClass('active');
  });

  $('.workflow-accordion').on('hide', function (e) {
    $(this).find('.accordion-toggle').not($(e.target)).removeClass('active');
  });

  $('#assessmentWorkflowChoose').on('change', function(){
    var id = $(this).val()
      , workflow = null;
    new Workflow.List({}).each(function(v){
      if(v.id == id){
        workflow = v;
      }
    });
    if(id == "new"){
      workflow = new Workflow({_new: true, title: "", tasks: [], reviews: []});
    }
    $("workflow-app").trigger("workflow_selected", workflow);
    $('#accordionContentReview').show();
    $('#accordionContentTasks').show();
    return;
    if($(this).val() == 'newWorkflow') {
      $('#regularWorkflowLabel').hide();
      $('#newWorkflowLabel').show();
      $('#newWorkflowTitle').show();
      $('.workflow-accordion .accordion-group .accordion-body').each(function(){
        $(this).addClass('in');
      });
      $('#accordionContentReview').show();
      $('#accordionContentTasks').show();
      $('#showTasksCount').html('3');
      $('#showReviewCount').html('2');
    } else if ($(this).val() == 'existingWorkflow') {
      $('.workflow-accordion .accordion-group .accordion-body').each(function(){
        $(this).addClass('in');
      });
      $('#accordionContentReview').show();
      $('#accordionContentTasks').show();
      $('#showTasksCount').html('3');
      $('#showReviewCount').html('2');
    } else {
      $('#regularWorkflowLabel').show();
      $('#newWorkflowLabel').hide();
      $('#newWorkflowTitle').hide();

      $('.workflow-accordion .accordion-group .accordion-body').each(function(){
        $(this).removeClass('in');
      });
      $('#accordionContentReview').hide();
      $('#accordionContentTasks').hide();
      $('#showTasksCount').html('0');
      $('#showReviewCount').html('0');
    }
  });

  $('body').on('click', '#addWorkflow', function() {
    $('#setupWorkflow').modal('hide');
    $('#workflowNotSet').hide();
    $('#workflowSet').show();
    $('#workflowTasksCount').html('3');
    $('#workflowReviewCount').html('2');
    $('#workflowTasks').show();
    $('#workflowReviews').show();
    $('#workflowFrequency').show();
    $('#workflowSetup').hide();
    $('#workflowEdit').show();
    $('#noWorkflow').hide();
  });

  $('body').on('mouseover', '.section-add', function() {
    var $this = $(this)
    ,   $sectionExpand = $this.closest('.section-expandable').find('.section-expander');

    $this.hide();
    $sectionExpand.show();
  });

  $('body').on('click', '#addSingleObjectTrigger', function() {
    $('#addSingleObject').show();
    $('#objectFooterUtility').hide();
  });

  $('body').on('click', '#addSingleControl', function() {
    $('#addSingleObject').hide();
    $('#addedObject').show();
    $('#objectsCounter').html('(5)');
    $('#objectsMainCounter').html('5');
    $('#objectFooterUtility').show();
    $('.section-expander').hide();
    $('.section-add').show();
    $('#noObjects').html('5 Objects selected').css('font-style','normal').css('color','#000');
    $('#startAssessment').removeClass('disabled');
  });

  $('body').on('click', '#cancelSingleControl', function() {
    $('#objectFooterUtility').show();
    $('#addSingleObject').hide();
    $('.section-expander').hide();
    $('.section-add').show();
  });

  $("#objectAll").click(function () {
    $(".object-check-single").prop('checked', $(this).prop('checked'));
    if($('#objectAll').attr('checked', true)) {
      $('#objectAdd').show();
    } else {
      $('#objectAdd').hide();
    }
  });

  $('body').on('click', '#objectAdd a', function() {
    $('#objectStep2').hide();
    $('#objectAdd').hide();
    $('#objectStep3').show();
    $('#objectsCounter').html('(4)');
    $('#objectsMainCounter').html('4');
  });

  $('body').on('click', '#addRule', function() {
    $('#newRule').show();
  });

  $('body').on('click', '#objectReview', function() {
    $('#objectStep1').hide();
    $('#objectStep2').show();
    $('#objectAdd').show();
  });

  $('body').on('click', '#addEntryTrigger', function() {
    $('#entryText').show();
    $(this).hide();
  });

  $('body').on('click', '#addEntryButton', function() {
    $('#newEntry').show();
    $('#addEntryTrigger').show();
    $('#entryText').hide();
    $('#entriesCount').html('2');
    $('#taskEntryCounterMain').html('1');
  });

  $('body').on('click', '#startObject', function() {
    $('#finishObject').show();
    $(this).hide();
  });

  $('body').on('click', '#startTask', function() {
    $(this).hide();
    $('#finishTask').show();
  });
  $('body').on('click', '#startTask2', function() {
    $(this).hide();
    $('#finishTask2').show();
  });
  $('body').on('click', '#startTask3', function() {
    $(this).hide();
    $('#finishTask3').show();
  });

  $('body').on('click', '#finishTask', function() {
    $('#verifyTask').show();
    $(this).hide();
  });

  $('body').on('click', '#finishTask2', function() {
    $(this).hide();
    $('#verifyTask2').show();
  });

  $('body').on('click', '#finishTaskSpecial', function() {
    $(this).hide();
    $('#verifyTaskSpecial').show();
  });

  $('body').on('click', '#finishTask3', function() {
    $(this).hide();
    $('#verifyTask3').show();
  });

  $('body').on('click', '#verifyTask', function() {
    $(this).closest('.tree-item').removeClass('rq-draft');
    $(this).closest('.tree-item').addClass('rq-accepted');
    $(this).hide();
    $('#taskDone').show();
  });

  $('body').on('click', '#verifyTask2', function() {
    $(this).closest('.tree-item').removeClass('rq-draft');
    $(this).closest('.tree-item').addClass('rq-accepted');
    $(this).hide();
    $('#taskDone2').show();
  });

  $('body').on('click', '#verifyTask3', function() {
    $(this).closest('.tree-item').removeClass('rq-draft');
    $(this).closest('.tree-item').addClass('rq-accepted');
    $(this).hide();
    $('#taskDone3').show();
  });

  $('body').on('click', '#peerReviewActive', function() {
    $(this).hide();
    $('#peerReview').show();
  });

  $('body').on('click', '#partyReviewActive', function() {
    $(this).hide();
    $('#partyReview').show();
  });

  $('body').on('click', '#peerReviewComplete', function() {
    $(this).hide();
    $('#reviewNoteDone').show();
    $('#addNote').hide();
  });

  $('body').on('click', '#partyReviewComplete', function() {
    $(this).hide();
    $('#reviewNoteDone2').show();
    $('#addNote2').hide();
    $('#finishObject').removeClass('disabled');
  });

  $('body').on('click', '#finishObject', function() {
    $(this).closest('.tree-item').removeClass('rq-amended-request').addClass('rq-accepted');
    $(this).hide();
    $('#objectMessage').show();
  });

  $('body').on('click', '#filterTrigger', function() {
    $('#objectStep2').hide();
    $('#objectStep1').show();
  });

  $('body').on('click', '#filterTriggerFooter', function() {
    $('#objectStep2').hide();
    $('#objectStep3').hide();
    $('#objectStep1').show();
  });

  $('body').on('click', '#addTaskGroup', function() {
    $('#TaskGroupItem').show();
    $('#TaskGroupCounter').html('1');
    $('#objectsMainCounter4').html('1');
    $('#workflowStart').removeClass('disabled');
  });

  $('body').on('click', '#cancelTaskGroup', function() {
    $('#addSingleObject').hide();
    $('#objectFooterUtility').show();
  });

  $('body').on('click', '#TaskDescription', function() {
    $('#TaskHolder').show();
    $('#TaskDescription').hide();
  });

  $('body').on('click', '#descriptionCancel', function() {
    $('#TaskHolder').hide();
    $('#TaskDescription').show();
  });

  $('body').on('click', '#descriptionSave', function() {
    $('#TaskHolder').hide();
    $('#TaskDescription').hide();
    $('#TaskUpdated').show();
  });

  $('body').on('click', '#objectAddTrigger', function() {
    $('#objectList').show();
    $('#objectWorkflowCounter').html('2');
  });

  $('body').on('click', '#taskAdd', function() {
    $('#taskList').show();
    $('#lockTrigger').show();
    $('#taskWorkflowCounter').html('3');
  });

  $("#taskLock").change(function () {
    if($(this).is(':checked')) {
      $('#taskAdd').addClass('disabled');
      $('.task-list .objective-selector a').addClass('disabled');
    } else {
      $('#taskAdd').removeClass('disabled');
      $('.task-list .objective-selector a').removeClass('disabled');
    }
  });

  $("body").on('change', '.object-check-single', function() {
    if($(this).is(':checked')) {
      $(this).closest('.tree-item').removeClass('disabled');
    } else {
      $(this).closest('.tree-item').addClass('disabled');
    }
  });

  $('body').on('click', '#titleChange', function() {
    $(this).closest('h3').hide();
    $('#taskGroupTitle').show();
  });

  $('body').on('click', '#editFieldSave', function() {
    $('#titleChange').closest('h3').show();
    $('#taskGroupTitle').hide();
  });

  $('body').on('click', '#editFieldCancel', function() {
    $('#titleChange').closest('h3').show();
    $('#taskGroupTitle').hide();
  });

  $('body').on('click', '#endWorkflowTrigger', function() {
    $('.internav .progress-object').addClass('finished');
    $('#endWorkflowTrigger').hide();
    $('.internav .inner-nav-button span.message').show();
    $('.header-message').show();
    $('.workflow-group').addClass('finished');
    $('.finished-number').show();
  });

  $('body').on('click', '#cancelEntry', function() {
    $('#entryText').hide();
    $('#addEntryTrigger').show();
  });

  $('body').on('click', '#editEntryTrigger', function() {
    $('#firstEntry').hide();
    $('#editEntry').show();
  });

  $('body').on('click', '#editEntrySave', function() {
    $('#firstEntry').show();
    $('#editEntry').hide();
  });

  $('body').on('click', '#editEntryCancel', function() {
    $('#firstEntry').show();
    $('#editEntry').hide();
  });

  $('#frequency').on('change', function(){
    if($(this).val() == 'one_time') {
      $('.frequency-wrap').hide();
      $('#one-time').show();
    } else if ($(this).val() == 'weekly') {
      $('.frequency-wrap').hide();
      $('#weekly').show();
    } else if ($(this).val() == 'monthly') {
      $('.frequency-wrap').hide();
      $('#monthly').show();
    } else if ($(this).val() == 'quarterly') {
      $('.frequency-wrap').hide();
      $('#quarterly').show();
    } else if ($(this).val() == 'annually') {
      $('.frequency-wrap').hide();
      $('#annually').show();
    } else if ($(this).val() == 'continuos') {
      $('.frequency-wrap').hide();
      $('#continuos').show();
    }
  });

  // Hide fields in modals
  $(".modal .hide").each(function() {
    var $this = $(this),
        $hideable = $(this).closest('[class*="span"].hideable'),
        $innerHide = $this.closest('[class*="span"]').find('.hideable'),
        $resetForm = $this.closest('.modal-body').find('.reset-form');

    $this.click(function() {
      $this.closest('.inner-hide').addClass('inner-hideable');
      $hideable.hide();
      $resetForm.show();

      for(var i=0; i < $this.closest('.hide-wrap.hideable').find('.inner-hideable').length; i++) {
        if(i == 1) {
          $this.closest('.inner-hide').parent('.hideable').hide();
        }
      }

    });

    $resetForm.click(function() {
      $this.closest('.inner-hide').removeClass('inner-hideable');
      $hideable.show();
      $('.inner-hide').parent('.hideable').show();
      $resetForm.hide();
    });
  });

});

// Grid View Example
/*
var dataView;
var grid;
var data = [];
var columns = [
  {id: "title", name: "Title", field: "title", width: 330, minWidth: 120, cssClass: "cell-title", editor: Slick.Editors.Text, validator: requiredFieldValidator, sortable: true},
  {id: "assignee", name: "Assignee", field: "assignee", width: 170, minWidth: 100, cssClass: "cell-assignee", editor: Slick.Editors.Auto, sortable: true},
  {id: "status", name: "Status", field: "status", width: 140, minWidth: 80, cssClass: "cell-status", options: "Assigned,Accepted,Completed", editor: Slick.Editors.Select, sortable: true},
  {id: "due-on", name: "Due on", field: "due-on", width: 140, minWidth: 80, cssClass: "cell-due-on", editor: Slick.Editors.Date, sortable: true}
];

var options = {
  editable: true,
  enableAddRow: true,
  enableCellNavigation: true,
  asyncEditorLoading: true,
  forceFitColumns: true,
  topPanelHeight: 25,
  rowHeight: 32,
};

var sortcol = "title";
var sortdir = 1;
var percentCompleteThreshold = 0;
var searchString = "";

function requiredFieldValidator(value) {
  if (value == null || value == undefined || !value.length) {
    return {valid: false, msg: "This is a required field"};
  }
  else {
    return {valid: true, msg: null};
  }
}

function myFilter(item, args) {
  if (args.searchString != "" && item["title"].indexOf(args.searchString) == -1) {
    return false;
  }

  return true;
}

function comparer(a, b) {
  var x = a[sortcol], y = b[sortcol];
  return (x == y ? 0 : (x > y ? 1 : -1));
}

function toggleFilterRow() {
  grid.setTopPanelVisibility(!grid.getOptions().showTopPanel);
}

$(function () {
  // prepare the data
  for (var i = 0; i < 500; i++) {
    var d = (data[i] = {});

    d["id"] = "id_" + i;
    d["num"] = i;
    d["title"] = "Collect documentation " + i;
    d["assignee"] = "Cassius Clay";
    d["status"] = "Assigned";
    d["due-on"] = "Due on: 01/05/13";
  }


  dataView = new Slick.Data.DataView({inlineFilters: true});
  grid = new Slick.Grid("#myGrid", dataView, columns, options);
  grid.setSelectionModel(new Slick.RowSelectionModel());

  var pager = new Slick.Controls.Pager(dataView, grid, $("#pager"));
  var columnpicker = new Slick.Controls.ColumnPicker(columns, grid, options);


  // move the filter panel defined in a hidden div into grid top panel
  $("#inlineFilterPanel")
      .appendTo(grid.getTopPanel())
      .show();

  grid.onCellChange.subscribe(function (e, args) {
    dataView.updateItem(args.item.id, args.item);
  });

  grid.onAddNewRow.subscribe(function (e, args) {
    var item = {"num": data.length, "id": "new_" + (Math.round(Math.random() * 10000)), "title": "New task", "assignee": "Cassius Clay", "status": "Assigned", "due-on": "Due on: 01/05/13"};
    $.extend(item, args.item);
    dataView.addItem(item);
  });

  grid.onKeyDown.subscribe(function (e) {
    // select all rows on ctrl-a
    if (e.which != 65 || !e.ctrlKey) {
      return false;
    }

    var rows = [];
    for (var i = 0; i < dataView.getLength(); i++) {
      rows.push(i);
    }

    grid.setSelectedRows(rows);
    e.preventDefault();
  });

  grid.onSort.subscribe(function (e, args) {
    sortdir = args.sortAsc ? 1 : -1;
    sortcol = args.sortCol.field;

    if ($.browser.msie && $.browser.version <= 8) {
      // using temporary Object.prototype.toString override
      // more limited and does lexicographic sort only by default, but can be much faster

      var percentCompleteValueFn = function () {
        var val = this["percentComplete"];
        if (val < 10) {
          return "00" + val;
        } else if (val < 100) {
          return "0" + val;
        } else {
          return val;
        }
      };

      // use numeric sort of % and lexicographic for everything else
      dataView.fastSort((sortcol == "percentComplete") ? percentCompleteValueFn : sortcol, args.sortAsc);
    } else {
      // using native sort with comparer
      // preferred method but can be very slow in IE with huge datasets
      dataView.sort(comparer, args.sortAsc);
    }
  });

  // wire up model events to drive the grid
  dataView.onRowCountChanged.subscribe(function (e, args) {
    grid.updateRowCount();
    grid.render();
  });

  dataView.onRowsChanged.subscribe(function (e, args) {
    grid.invalidateRows(args.rows);
    grid.render();
  });

  dataView.onPagingInfoChanged.subscribe(function (e, pagingInfo) {
    var isLastPage = pagingInfo.pageNum == pagingInfo.totalPages - 1;
    var enableAddRow = isLastPage || pagingInfo.pageSize == 0;
    var options = grid.getOptions();

    if (options.enableAddRow != enableAddRow) {
      grid.setOptions({enableAddRow: enableAddRow});
    }
  });


  var h_runfilters = null;

  // wire up the slider to apply the filter to the model
  $("#pcSlider,#pcSlider2").slider({
    "range": "min",
    "slide": function (event, ui) {
      Slick.GlobalEditorLock.cancelCurrentEdit();

      if (percentCompleteThreshold != ui.value) {
        window.clearTimeout(h_runfilters);
        h_runfilters = window.setTimeout(updateFilter, 10);
        percentCompleteThreshold = ui.value;
      }
    }
  });


  // wire up the search textbox to apply the filter to the model
  $("#txtSearch,#txtSearch2").keyup(function (e) {
    Slick.GlobalEditorLock.cancelCurrentEdit();

    // clear on Esc
    if (e.which == 27) {
      this.value = "";
    }

    searchString = this.value;
    updateFilter();
  });

  function updateFilter() {
    dataView.setFilterArgs({
      searchString: searchString
    });
    dataView.refresh();
  }

  $("#btnSelectRows").click(function () {
    if (!Slick.GlobalEditorLock.commitCurrentEdit()) {
      return;
    }

    var rows = [];
    for (var i = 0; i < 10 && i < dataView.getLength(); i++) {
      rows.push(i);
    }

    grid.setSelectedRows(rows);
  });


  // initialize the model after all the events have been hooked up
  dataView.beginUpdate();
  dataView.setItems(data);
  dataView.setFilterArgs({
    searchString: searchString
  });
  dataView.setFilter(myFilter);
  dataView.endUpdate();

  // if you don't want the items that are not visible (due to being filtered out
  // or being on a different page) to stay selected, pass 'false' to the second arg
  dataView.syncGridSelection(grid, true);

  $("#gridContainer").resizable();

})
*/