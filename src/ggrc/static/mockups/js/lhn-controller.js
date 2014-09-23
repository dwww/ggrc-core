/*!
    Copyright (C) 2013 Google Inc., authors, and contributors <see AUTHORS file>
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
    Created By: brad@reciprocitylabs.com
    Maintained By: brad@reciprocitylabs.com
*/

//require can.jquery-all


function resize_areas() {
  var $window
  ,   $lhs
  ,   $lhsHolder
  ,   $area
  ,   $header
  ,   $footer
  ,   $innerNav
  ,   $objectArea
  ,   $bar
  ,   winHeight
  ,   winWidth
  ,   objectWidth
  ,   headerWidth
  ,   lhsWidth
  ,   footerMargin
  ,   internavHeight
  ;

  $window = $(window);
  $lhs = $(".lhs");
  $lhsHolder = $(".lhs-holder");
  $footer = $(".footer");
  $header = $(".header-content");
  $innerNav = $(".inner-nav");
  $objectArea = $(".object-area");
  $area = $(".area");
  $bar = $(".bar-v");

  winHeight = $window.height();
  winWidth = $window.width();
  lhsHeight = winHeight - 70;
  footerMargin = lhsHeight;
  internavHeight = lhsHeight - 50;
  lhsWidth = $lhsHolder.width();
  barWidth = $bar.is(":visible") ? $bar.outerWidth() : 0;
  internavWidth = $innerNav.width() || 0; // || 0 for pages without inner-nav
  objectWidth = winWidth - lhsWidth - internavWidth - barWidth;
  headerWidth = winWidth - lhsWidth;

  $lhsHolder.css("height",lhsHeight);
  $bar.css("height",lhsHeight);
  $footer.css("margin-top",footerMargin);
  $innerNav.css("height",internavHeight);
  $header.css("width",headerWidth);
  $objectArea
    .css("margin-left",internavWidth)
    .css("height",internavHeight -30)
    .css("width",objectWidth)
    ;

}

var LHN = can.Control({
    defaults: {
    }
}, {
    init: function() {
      var self = this
        ;

      this.obs = new can.Observe();

      this.init_lhn();
    }

  , init_lhn: function() {
      var self = this;

        self.size = self.min_lhn_size;
        self.objnav_size = 200;
        self.resize_lhn(self.size);
        self.resize_objnav(self.lhn_width() + self.objnav_size);
        // Collapse the LHN if they did it on a previous page
        self.collapsed = false;
        self.collapsed && self.toggle_lhs();
    }
  , lhn_width : function(){
      return $(".lhs-holder").width()+8;
  }
  , hide_lhn: function() {
      var $area = $(".area")
        , $lhsHolder = $(".lhs-holder")
        , $bar = $('.bar-v')
        ;

      this.element.hide();
      $lhsHolder.css("width", 0);
      $area.css("margin-left", 0);
      $bar.hide();

      window.resize_areas();
    }

  , toggle_lhs: function() {
      var $lhs = $("#lhs")
        , $lhsHolder = $(".lhs-holder")
        , $area = $(".area")
        , $bar = $("#lhn > .bar-v")
        , $obj_bar = $(".objnav.bar-v")
        , $search = $('.widgetsearch')
        ;
      if($lhs.hasClass("lhs-closed")) {
        $lhs.removeClass("lhs-closed");
        $bar.removeClass("bar-closed");
        $lhsHolder.css("width", this.size + "px");
        $area.css("margin-left", (this.size + 8) + "px");
        $bar.css("left", this.size + "px");
        $search.width(this.size - 100);
      } else {
        $lhs.addClass("lhs-closed");
        $bar.addClass("bar-closed");
        $lhsHolder.css("width","40px");
        $area.css("margin-left","48px");
        $bar.css("left", "40px");
      }

      window.resize_areas();
      $(window).trigger('resize');
      $obj_bar.css("left", (this.objnav_size + this.lhn_width()) + "px");
    }
  , min_lhn_size : 240
  , min_objnav_size : 44
  , mousedown : false
  , dragged : false
  , resize_lhn : function(resize){
    var $lhs = $("#lhs")
    , $lhsHolder = $(".lhs-holder")
    , $area = $(".area")
    , $bar = $("#lhn>.bar-v")
    , $obj_bar = $(".objnav.bar-v")
    , $search = $('.widgetsearch')
    ;
    if(resize < this.min_lhn_size/2 && !$lhs.hasClass("lhs-closed")) this.toggle_lhs();
    if(resize < this.min_lhn_size) return;
    if($lhs.hasClass("lhs-closed")) this.toggle_lhs();
    $lhsHolder.width(resize);

    var a = (resize) + "px";
    var b = (resize+8) + "px"
    $area.css("margin-left",  b);

    $bar.css("left", a)

    $search.width(resize - 150);
    window.resize_areas();
    //$(window).trigger('resize');
    $obj_bar.css("left", (this.objnav_size + this.lhn_width()) + "px");
  }
  , resize_objnav : function(resize){

    var $object_area = $(".object-area")
      , $object_nav = $(".inner-nav")
      , $object_bar = $('.objnav.bar-v')
      , collapsed = false
      , size = resize - this.lhn_width();
      ;
    if(size < this.min_objnav_size) return;
    $object_nav.width(size);
    $object_bar.css('left', resize);
    window.resize_areas();
    //$(window).trigger('resize');
  }
  , "{window} resize" : function(el, ev){
    this.resize_lhn(this.lhn_width()-8);
    this.resize_objnav(this.lhn_width() + this.objnav_size);
  }
  , "{window} mousedown" : function(el, ev) {
    var $target = $(ev.target);
    if(!$target.hasClass('bar-v'))
      return;
    this.objnav = $target.hasClass('objnav');
    this.mousedown = true;
    this.dragged = false;
  }
  , "{window} mousemove" : function(el, ev){
    if(!this.mousedown){
      return;
    }

    ev.preventDefault();
    this.dragged = true;
    if(!this.objnav){
      this.size = ev.pageX;
      this.resize_lhn(this.size, el);
    }
    else{
      this.objnav_size = ev.pageX - this.lhn_width();
      this.resize_objnav(ev.pageX);
    }
  }
  , "{window} mouseup" : function(el, ev){
    var self = this;
    if(!this.mousedown) return;

    this.mousedown = false;
    if(!this.dragged && !this.objnav){
      this.toggle_lhs();
      return;
    }
    self.size = Math.max(self.size, this.min_lhn_size);
    self.objnav_size = Math.max(self.objnav_size, self.min_objnav_size);
  }
});



$(function() {
  new LHN('#lhn', {});
});
