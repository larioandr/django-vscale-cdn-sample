//
// Original code was taken from https://github.com/Foliotek/Croppie/blob/master/demo/demo.js
//
(function ($) {
  var addUniqueClass = function (elem, klass) {
    if (!elem.hasClass(klass)) {
      elem.addClass(klass);
    }
  };

  // Define a default action - popup an image in a separate window.
  // In real world, here we will send an AJAX POST.
  var popupImage = function (src) {
    console.log(typeof(src));
    Swal.fire({
      imageUrl: src
    });
  };


  ////////////////////////////////////////////////////////////////////
  // Plugin 'avatarUpload'
  ////////////////////////////////////////////////////////////////////
  $.fn.avatarUpload = function(options) {
    var $wrap = this.find('.avatar-upload-wrap');
    var $msg = this.find('.avatar-upload-msg');
    var $frame = $wrap.find('.avatar-upload-frame');
    var $input = this.find('.avatar-file-input input');
    var $controls = this.find('.avatar-upload-control');

    // This function loads data from the file input into the croppie frame.
    var readFile = function (input) {
      if (input.files && input.files[0]) {
        var reader = new FileReader();
        reader.onload = function(e) {
          addUniqueClass($wrap, 'ready');
          addUniqueClass($msg, 'hidden');
          $frame.croppie('bind', {url: e.target.result});
        };
        reader.readAsDataURL(input.files[0]);
      }
    };

    var attach = function (settings) {
      var $result = $controls.filter('.avatar-upload-control-result');
      var $rotateLeftCtrl = $controls.filter('.avatar-upload-control-rotate-left');
      var $rotateRightCtrl = $controls.filter('.avatar-upload-control-rotate-right');

      $frame.croppie({
        viewport: {width: settings.intSize, height: settings.intSize, type: 'circle'},
        boundary: {width: settings.extSize, height: settings.extSize},
        enableOrientation: true
      });

      $input.on('change', function() {
        readFile(this);
      });

      $result.on('click', function(ev) {
        $frame.croppie('result', {type: 'canvas', size: 'viewport'})
          .then(settings.fn);
      });

      $rotateLeftCtrl.on('click', () => { $frame.croppie('rotate', 90); });
      $rotateRightCtrl.on('click', () => { $frame.croppie('rotate', -90); });

      $('.avatar-upload-form').submit(function (event) {

      });

    };

    //
    // --- main function ---
    //
    var settings = $.extend({
      extSize: 300,
      intSize: 250,
      fn: popupImage
    }, options);

    attach(settings);

    return this;
  };
}(jQuery));
