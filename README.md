# ICONCLASS

A multilingual subject classification system for cultural content
For more information see: http://www.iconclass.org/

Made by Hans Brandhorst <jpjbrand@xs4all.nl> & Etienne Posthumus <eposthumus@gmail.com>

    ...with lots of support from a global cast of many, many people since 1972.

## Example usage:

```python
from iconclass import init

ic = init()
a = ic["53A2"]

print(a)
print(repr(a))
print(a())
print(a('de'))

for child in a:
    print(child('it'))

for p in a.path():
    print(repr(p))
```
