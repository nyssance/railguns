// Drawer https://material.io/components/web/catalog/drawers/
const element = document.querySelector('.mdc-drawer--temporary')
if (element) {
    const drawer = new mdc.drawer.MDCTemporaryDrawer(element)
    const navigationIcon = document.querySelector('.mdc-top-app-bar__navigation-icon')
    if (navigationIcon) {
        navigationIcon.addEventListener('click', () => drawer.open = true)
    }
} else {
    console.log('没有 Drawer')
}
