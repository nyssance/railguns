'use strict'

// Drawer https://material.io/components/web/catalog/drawers/
let element = document.querySelector('.mdc-temporary-drawer')
if (element != null) {
    let drawer = new mdc.drawer.MDCTemporaryDrawer(element)
    document.querySelector('.mdc-toolbar__menu-icon').addEventListener('click', () => drawer.open = true)
} else {
    console.log('没有 Drawer')
}
