/*
 * accessibility.c
 * Copyright (C) 2024 Kovid Goyal <kovid at kovidgoyal.net>
 *
 * Distributed under terms of the GPL3 license.
 */

#include "data-types.h"
#include "state.h"
#include "screen.h"
#include "lineops.h"
#include "line-buf.h"
#include <structmember.h>

#ifdef __APPLE__
#include <CoreFoundation/CoreFoundation.h>

// Forward declarations for Objective-C functions (implemented in cocoa_window.m)
extern void cocoa_set_accessibility_value_impl(const char* text);
extern const char* cocoa_get_accessibility_value_impl(void);
extern void cocoa_post_accessibility_notification(const char* notification_name);
extern const char* cocoa_get_terminal_text_for_window(void* window_handle);
extern void cocoa_insert_text_for_window(void* window_handle, const char* text);
#endif

// Helper function to get Python Window object from window ID
static PyObject*
get_window_from_id(PyObject *window_id_obj) {
    if (!global_state.boss) {
        PyErr_SetString(PyExc_RuntimeError, "Boss object not available");
        return NULL;
    }
    
    // Get the window_id_map from Boss
    PyObject *window_id_map = PyObject_GetAttrString(global_state.boss, "window_id_map");
    if (!window_id_map) {
        PyErr_SetString(PyExc_RuntimeError, "Could not get window_id_map from Boss");
        return NULL;
    }
    
    // Get the window from the map
    PyObject *window = PyObject_CallMethod(window_id_map, "get", "O", window_id_obj);
    Py_DECREF(window_id_map);
    
    if (!window || window == Py_None) {
        if (window) Py_DECREF(window);
        PyErr_Format(PyExc_ValueError, "Window with ID %ld not found", PyLong_AsLong(window_id_obj));
        return NULL;
    }
    
    return window;
}

// Helper function to get Screen object from Window
static PyObject*
get_screen_from_window(PyObject *window) {
    PyObject *screen = PyObject_GetAttrString(window, "screen");
    if (!screen) {
        PyErr_SetString(PyExc_RuntimeError, "Could not get screen from Window");
        return NULL;
    }
    return screen;
}

static PyObject*
get_terminal_text(PyObject *self UNUSED, PyObject *args) {
    PyObject *window_id_obj;
    if (!PyArg_ParseTuple(args, "O", &window_id_obj)) return NULL;
    
    // Get the Window object
    PyObject *window = get_window_from_id(window_id_obj);
    if (!window) return NULL;
    
    // Get the Screen object
    PyObject *screen = get_screen_from_window(window);
    Py_DECREF(window);
    if (!screen) return NULL;
    
    // Get the linebuf from screen
    PyObject *linebuf = PyObject_GetAttrString(screen, "linebuf");
    if (!linebuf) {
        Py_DECREF(screen);
        PyErr_SetString(PyExc_RuntimeError, "Could not get linebuf from Screen");
        return NULL;
    }
    
    // Get the historybuf from screen (for scrollback)
    PyObject *historybuf = PyObject_GetAttrString(screen, "historybuf");
    if (!historybuf) {
        Py_DECREF(screen);
        Py_DECREF(linebuf);
        PyErr_SetString(PyExc_RuntimeError, "Could not get historybuf from Screen");
        return NULL;
    }
    
    // Build the complete text: historybuf + linebuf
    PyObject *result = PyUnicode_FromString("");  // Start with empty string
    
    // Get text from historybuf if it has content
    PyObject *historybuf_str = PyObject_CallMethod(historybuf, "as_text", "");
    if (historybuf_str && historybuf_str != Py_None) {
        PyObject *temp = PyUnicode_Concat(result, historybuf_str);
        Py_DECREF(result);
        result = temp;
        Py_DECREF(historybuf_str);
    }
    
    // Get text from linebuf (current visible lines)
    PyObject *linebuf_str = PyObject_Str(linebuf);
    if (linebuf_str) {
        // Add a newline between history and current if history exists
        if (PyUnicode_GET_LENGTH(result) > 0) {
            PyObject *newline = PyUnicode_FromString("\n");
            PyObject *temp = PyUnicode_Concat(result, newline);
            Py_DECREF(result);
            Py_DECREF(newline);
            result = temp;
        }
        
        PyObject *temp = PyUnicode_Concat(result, linebuf_str);
        Py_DECREF(result);
        result = temp;
        Py_DECREF(linebuf_str);
    }
    
    Py_DECREF(screen);
    Py_DECREF(linebuf);
    Py_DECREF(historybuf);
    
    return result;
}

static PyObject*
get_cursor_text_position(PyObject *self UNUSED, PyObject *args) {
    PyObject *window_id_obj;
    if (!PyArg_ParseTuple(args, "O", &window_id_obj)) return NULL;
    
    // Get the Window object
    PyObject *window = get_window_from_id(window_id_obj);
    if (!window) return NULL;
    
    // Get the Screen object
    PyObject *screen = get_screen_from_window(window);
    Py_DECREF(window);
    if (!screen) return NULL;
    
    // Get the cursor object from screen
    PyObject *cursor = PyObject_GetAttrString(screen, "cursor");
    if (!cursor) {
        Py_DECREF(screen);
        PyErr_SetString(PyExc_RuntimeError, "Could not get cursor from Screen");
        return NULL;
    }
    
    // Get cursor x and y positions
    PyObject *x_obj = PyObject_GetAttrString(cursor, "x");
    PyObject *y_obj = PyObject_GetAttrString(cursor, "y");
    Py_DECREF(cursor);
    
    if (!x_obj || !y_obj) {
        Py_XDECREF(x_obj);
        Py_XDECREF(y_obj);
        Py_DECREF(screen);
        PyErr_SetString(PyExc_RuntimeError, "Could not get cursor position");
        return NULL;
    }
    
    long x = PyLong_AsLong(x_obj);
    long y = PyLong_AsLong(y_obj);
    Py_DECREF(x_obj);
    Py_DECREF(y_obj);
    
    // Get the number of columns to calculate offset
    PyObject *columns_obj = PyObject_GetAttrString(screen, "columns");
    if (!columns_obj) {
        Py_DECREF(screen);
        PyErr_SetString(PyExc_RuntimeError, "Could not get columns from Screen");
        return NULL;
    }
    long columns = PyLong_AsLong(columns_obj);
    Py_DECREF(columns_obj);
    
    // Get the scrolled_by value for history offset
    PyObject *scrolled_by_obj = PyObject_GetAttrString(screen, "scrolled_by");
    long scrolled_by = 0;
    if (scrolled_by_obj) {
        scrolled_by = PyLong_AsLong(scrolled_by_obj);
        Py_DECREF(scrolled_by_obj);
    }
    
    // Get historybuf to count history lines
    PyObject *historybuf = PyObject_GetAttrString(screen, "historybuf");
    long history_lines = 0;
    if (historybuf) {
        PyObject *count_obj = PyObject_CallMethod(historybuf, "__len__", "");
        if (count_obj) {
            history_lines = PyLong_AsLong(count_obj);
            Py_DECREF(count_obj);
        }
        Py_DECREF(historybuf);
    }
    
    Py_DECREF(screen);
    
    // Calculate the text position
    // Position = (history_lines - scrolled_by + y) * columns + x
    long position = (history_lines - scrolled_by + y) * columns + x;
    
    return PyLong_FromLong(position);
}

// Helper function to process voice commands
static const char*
process_voice_command(const char* text) {
    // Check for common voice commands
    if (strcmp(text, "new line") == 0 || strcmp(text, "newline") == 0) return "\n";
    if (strcmp(text, "tab") == 0) return "\t";
    if (strcmp(text, "escape") == 0) return "\x1b";
    if (strcmp(text, "space") == 0) return " ";
    if (strcmp(text, "backspace") == 0) return "\x7f";
    if (strcmp(text, "delete") == 0) return "\x7f";
    if (strcmp(text, "enter") == 0 || strcmp(text, "return") == 0) return "\r";
    
    // Return original text if not a command
    return text;
}

static PyObject*
insert_text_at_cursor(PyObject *self UNUSED, PyObject *args) {
    PyObject *window_id_obj;
    const char *text;
    if (!PyArg_ParseTuple(args, "Os", &window_id_obj, &text)) return NULL;
    
    // Process potential voice commands
    const char *processed_text = process_voice_command(text);
    
    // Get the Window object
    PyObject *window = get_window_from_id(window_id_obj);
    if (!window) return NULL;
    
    // Use the Window's write_to_child method to send text to the terminal
    // This respects terminal modes and goes through the proper input pipeline
    PyObject *result = PyObject_CallMethod(window, "write_to_child", "s", processed_text);
    Py_DECREF(window);
    
    if (!result) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to write text to terminal");
        return NULL;
    }
    Py_DECREF(result);
    
    Py_RETURN_NONE;
}

static PyObject*
set_cursor_position(PyObject *self UNUSED, PyObject *args) {
    PyObject *window_id_obj;
    int position;
    if (!PyArg_ParseTuple(args, "Oi", &window_id_obj, &position)) return NULL;
    
    // Stub implementation - will set cursor position later
    Py_RETURN_NONE;
}

static PyObject*
get_number_of_characters(PyObject *self UNUSED, PyObject *args) {
    PyObject *window_id_obj;
    if (!PyArg_ParseTuple(args, "O", &window_id_obj)) return NULL;
    
    // Get the terminal text to count characters
    PyObject *text = get_terminal_text(self, args);
    if (!text) return NULL;
    
    // Get the length of the text
    Py_ssize_t length = PyUnicode_GET_LENGTH(text);
    Py_DECREF(text);
    
    return PyLong_FromSsize_t(length);
}

static PyObject*
get_visible_character_range(PyObject *self UNUSED, PyObject *args) {
    PyObject *window_id_obj;
    if (!PyArg_ParseTuple(args, "O", &window_id_obj)) return NULL;
    
    // Get the Window object
    PyObject *window = get_window_from_id(window_id_obj);
    if (!window) return NULL;
    
    // Get the Screen object
    PyObject *screen = get_screen_from_window(window);
    Py_DECREF(window);
    if (!screen) return NULL;
    
    // Get screen dimensions
    PyObject *columns_obj = PyObject_GetAttrString(screen, "columns");
    PyObject *lines_obj = PyObject_GetAttrString(screen, "lines");
    
    if (!columns_obj || !lines_obj) {
        Py_XDECREF(columns_obj);
        Py_XDECREF(lines_obj);
        Py_DECREF(screen);
        PyErr_SetString(PyExc_RuntimeError, "Could not get screen dimensions");
        return NULL;
    }
    
    long columns = PyLong_AsLong(columns_obj);
    long lines = PyLong_AsLong(lines_obj);
    Py_DECREF(columns_obj);
    Py_DECREF(lines_obj);
    
    // Get scrolled_by value
    PyObject *scrolled_by_obj = PyObject_GetAttrString(screen, "scrolled_by");
    long scrolled_by = 0;
    if (scrolled_by_obj) {
        scrolled_by = PyLong_AsLong(scrolled_by_obj);
        Py_DECREF(scrolled_by_obj);
    }
    
    // Get historybuf to count history lines
    PyObject *historybuf = PyObject_GetAttrString(screen, "historybuf");
    long history_lines = 0;
    if (historybuf) {
        PyObject *count_obj = PyObject_CallMethod(historybuf, "__len__", "");
        if (count_obj) {
            history_lines = PyLong_AsLong(count_obj);
            Py_DECREF(count_obj);
        }
        Py_DECREF(historybuf);
    }
    
    Py_DECREF(screen);
    
    // Calculate visible range
    // Start position = (history_lines - scrolled_by) * columns
    // Length = lines * columns (visible area)
    long start = (history_lines - scrolled_by) * columns;
    long length = lines * columns;
    
    // Ensure start is not negative
    if (start < 0) start = 0;
    
    PyObject *result = PyTuple_New(2);
    PyTuple_SET_ITEM(result, 0, PyLong_FromLong(start));
    PyTuple_SET_ITEM(result, 1, PyLong_FromLong(length));
    return result;
}

static PyObject*
post_accessibility_notification(PyObject *self UNUSED, PyObject *args) {
    PyObject *window_id_obj;
    const char *notification_type;
    if (!PyArg_ParseTuple(args, "Os", &window_id_obj, &notification_type)) return NULL;
    
#ifdef __APPLE__
    // Map notification types to Cocoa constants
    if (strcmp(notification_type, "value_changed") == 0) {
        cocoa_post_accessibility_notification("NSAccessibilityValueChangedNotification");
    } else if (strcmp(notification_type, "selection_changed") == 0) {
        cocoa_post_accessibility_notification("NSAccessibilitySelectedTextChangedNotification");
    } else if (strcmp(notification_type, "focus_changed") == 0) {
        cocoa_post_accessibility_notification("NSAccessibilityFocusedUIElementChangedNotification");
    } else if (strcmp(notification_type, "layout_changed") == 0) {
        cocoa_post_accessibility_notification("NSAccessibilityLayoutChangedNotification");
    }
#endif
    
    Py_RETURN_NONE;
}

// Cocoa window functions for accessibility
static PyObject*
cocoa_get_accessibility_role(PyObject *self UNUSED, PyObject *args UNUSED) {
#ifdef __APPLE__
    // Should return NSAccessibilityTextAreaRole
    return PyUnicode_FromString("AXTextArea");
#else
    Py_RETURN_NONE;
#endif
}

static PyObject*
cocoa_get_accessibility_value(PyObject *self UNUSED, PyObject *window_id_obj) {
    (void)window_id_obj;  // Will use later
#ifdef __APPLE__
    const char* value = cocoa_get_accessibility_value_impl();
    if (value) {
        return PyUnicode_FromString(value);
    }
    return PyUnicode_FromString("");
#else
    Py_RETURN_NONE;
#endif
}

static PyObject*
cocoa_set_accessibility_value(PyObject *self UNUSED, PyObject *args) {
    PyObject *window_id_obj;
    const char *text;
    if (!PyArg_ParseTuple(args, "Os", &window_id_obj, &text)) return NULL;
    
#ifdef __APPLE__
    cocoa_set_accessibility_value_impl(text);
#endif
    
    Py_RETURN_NONE;
}

static PyMethodDef accessibility_methods[] = {
    // Python accessibility API
    {"accessibility_get_terminal_text", get_terminal_text, METH_VARARGS, "Get terminal buffer text"},
    {"accessibility_get_cursor_text_position", get_cursor_text_position, METH_VARARGS, "Get cursor position as text offset"},
    {"accessibility_insert_text_at_cursor", insert_text_at_cursor, METH_VARARGS, "Insert text at cursor"},
    {"accessibility_set_cursor_position", set_cursor_position, METH_VARARGS, "Set cursor to text position"},
    {"accessibility_get_number_of_characters", get_number_of_characters, METH_VARARGS, "Get total character count"},
    {"accessibility_get_visible_character_range", get_visible_character_range, METH_VARARGS, "Get visible text range"},
    {"accessibility_post_notification", post_accessibility_notification, METH_VARARGS, "Post accessibility notification"},
    
    // Cocoa accessibility functions
    {"get_accessibility_role", cocoa_get_accessibility_role, METH_NOARGS, "Get NSAccessibility role"},
    {"get_accessibility_value", cocoa_get_accessibility_value, METH_O, "Get NSAccessibility value"},
    {"set_accessibility_value", cocoa_set_accessibility_value, METH_VARARGS, "Set NSAccessibility value"},
    
    {NULL, NULL, 0, NULL}  // Sentinel
};

bool
init_accessibility(PyObject *module) {
    // Add accessibility methods to the module
    if (PyModule_AddFunctions(module, accessibility_methods) != 0) {
        return false;
    }
    
    // Add accessibility constants
#ifdef __APPLE__
    PyModule_AddStringConstant(module, "ACCESSIBILITY_PLATFORM", "macos");
#else
    PyModule_AddStringConstant(module, "ACCESSIBILITY_PLATFORM", "unsupported");
#endif
    
    return true;
}
