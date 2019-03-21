(function ($) {
  //////////////////////////////
  // Defining the plugin
  $.fn.ubioFileInput = function () {
    const label = this.find('.ubio-file-name');
    const input = this.find('input[type="file"]');
    input.on('change', function () {
      if (this.files && this.files[0]) {
        label.text(this.files[0].name);
      }
    });
    return this;
  };

  //////////////////////////////
  // Associating the plugin
  $('.ubio-file').ubioFileInput();
}(jQuery));
