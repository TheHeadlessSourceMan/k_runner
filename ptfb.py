from pywinauto import Desktop

app=Desktop(backend="uia").child_window(
    class="WindowsForms10.Window.8.app.0.27c59a_r8_ad1",
    title="layoutControl1")
app.doubleclick((870,433))
app.sendkeys('admin[tab]admin[enter]')
