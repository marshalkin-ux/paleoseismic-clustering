from html.parser import HTMLParser
class V(HTMLParser): pass
v = V()
v.feed(open('presentation/project_showcase.html', encoding='utf-8').read())
size = len(open('presentation/project_showcase.html','rb').read())
print("OK, size:", size, "bytes")
