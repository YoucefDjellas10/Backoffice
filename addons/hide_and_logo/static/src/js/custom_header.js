odoo.define('hide_and_logo.custom_header', function (require) {
    "use strict";

    var WebClient = require('web.WebClient');
    WebClient.include({
        start: function () {
            var self = this;
            return this._super().then(function () {
                var $user_menu = self.$('.o_user_menu');
                if ($user_menu.length) {
                    var $logo = $('<img>', {
                        src: '/hide_and_logo/static/src/img/logo.png',
                        alt: 'Logo'
                    });
                    $user_menu.prepend($logo);
                }
            });
        },
    });
});
