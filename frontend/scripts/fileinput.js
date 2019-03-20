(function ($) {
  //////////////////////////////
  // Defining the plugin
  $.fn.ubioFileInput = function () {
    const label = this.find('.ubio-file-name');
    const input = this.find('input[type="file"]');
    input.on('change', function () {
      if (this.files && this.files[0]) {
        console.log('FILE: ', this.files[0].name);
        label.text(this.files[0].name);
      }
    });
    return this;
  };

  //////////////////////////////
  // Associating the plugin
  console.log('* binding');
  $('.ubio-file').ubioFileInput();
}(jQuery));
console.log('* fileinput.js');