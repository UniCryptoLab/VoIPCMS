# -*- coding: utf-8 -*-
#!/usr/bin/python

def is_not_empty_null(val):
    if val is None:
        return False
    if val == '':
        return False
    return True

