'use strict';

// Drawer https://material.io/components/web/catalog/drawers/
var element = document.querySelector('.mdc-drawer--temporary');
if (element) {
    var drawer = new mdc.drawer.MDCTemporaryDrawer(element);
    var navigationIcon = document.querySelector('.mdc-top-app-bar__navigation-icon');
    if (navigationIcon) {
        navigationIcon.addEventListener('click', function () {
            return drawer.open = true;
        });
    }
} else {
    console.log('没有 Drawer');
}