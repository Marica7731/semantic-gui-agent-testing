from sgat.android.executor import parse_bounds, parse_uiautomator_xml

SAMPLE_DUMP = """<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>
<hierarchy rotation="0">
  <node index="0" text="" resource-id="" class="android.widget.FrameLayout" package="com.example"
        content-desc="" checkable="false" checked="false" clickable="false" enabled="true"
        focused="false" focused-search="false" scrollable="false" long-clickable="false"
        password="false" selected="false" bounds="[0,0][1080,2400]">
    <node index="1" text="OK" resource-id="com.example:id/ok" class="android.widget.Button"
          package="com.example" content-desc="confirm" checkable="false" clickable="true"
          enabled="true" bounds="[100,200][300,260]"/>
  </node>
</hierarchy>"""


def test_parse_bounds():
    assert parse_bounds("[10,20][30,40]") == (10, 20, 30, 40)


def test_parse_uiautomator_xml_builds_ui_tree():
    screen = parse_uiautomator_xml(SAMPLE_DUMP)
    assert screen.package == "com.example"
    button = next(n for n in screen.nodes() if n.text == "OK")
    assert button.class_name == "android.widget.Button"
    assert button.resource_id == "com.example:id/ok"
    assert button.content_desc == "confirm"
    assert button.clickable and button.enabled
    assert button.bounds == (100, 200, 300, 260)
    assert button.center() == (200, 230)
