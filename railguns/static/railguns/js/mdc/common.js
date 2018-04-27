'use strict'

// Drawer https://material.io/components/web/catalog/drawers/
let element = document.querySelector('.mdc-drawer--temporary')
if (element) {
    let drawer = new mdc.drawer.MDCTemporaryDrawer(element)
    let navigationIcon = document.querySelector('.mdc-top-app-bar__navigation-icon')
    if (navigationIcon) {
        navigationIcon.addEventListener('click', () => drawer.open = true)
    }
} else {
    console.log('没有 Drawer')
}
