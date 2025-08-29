/*
 * accessibility.c
 * Copyright (C) 2024 Kovid Goyal <kovid at kovidgoyal.net>
 *
 * Distributed under terms of the GPL3 license.
 */

#include "data-types.h"
#include "screen.h"
#include "lineops.h"
#include <structmember.h>

#ifdef __APPLE__
#include <CoreFoundation/CoreFoundation.h>

// Forward declarations for Objective-C functions (will be implemented in cocoa_window.m)
// TODO: Uncomment when implemented in cocoa_window.m
// extern void cocoa_set_accessibility_value_impl(const char* text);
// extern const char* cocoa_get_accessibility_value_impl(void);
// extern void cocoa_post_accessibility_notification(const char* notification_name);
#endif

static PyObject*
get_terminal_text(PyObject *self UNUSED, PyObject *args) {
    PyObject *window_id_obj;
    if (!PyArg_ParseTuple(args, "O", &window_id_obj)) return NULL;
    
    // Stub implementation - will connect to Screen later
    return PyUnicode_FromString("");
}

static PyObject*
get_cursor_text_position(PyObject *self UNUSED, PyObject *args) {
    PyObject *window_id_obj;
    if (!PyArg_ParseTuple(args, "O", &window_id_obj)) return NULL;
    
    // Stub implementation - will calculate cursor offset later
    return PyLong_FromLong(0);
}

static PyObject*
insert_text_at_cursor(PyObject *self UNUSED, PyObject *args) {
    PyObject *window_id_obj;
    const char *text;
    if (!PyArg_ParseTuple(args, "Os", &window_id_obj, &text)) return NULL;
    
    // Stub implementation - will insert text later
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
    
    // Stub implementation - will count characters later
    return PyLong_FromLong(0);
}

static PyObject*
get_visible_character_range(PyObject *self UNUSED, PyObject *args) {
    PyObject *window_id_obj;
    if (!PyArg_ParseTuple(args, "O", &window_id_obj)) return NULL;
    
    // Stub implementation - will calculate visible range later
    PyObject *result = PyTuple_New(2);
    PyTuple_SET_ITEM(result, 0, PyLong_FromLong(0));
    PyTuple_SET_ITEM(result, 1, PyLong_FromLong(0));
    return result;
}

static PyObject*
post_accessibility_notification(PyObject *self UNUSED, PyObject *args) {
    const char *notification_type;
    if (!PyArg_ParseTuple(args, "s", &notification_type)) return NULL;
    
#ifdef __APPLE__
    // TODO: Will connect to Objective-C layer later
    // cocoa_post_accessibility_notification(notification_type);
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
    // Stub - will get terminal text later
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
    // TODO: Stub - will insert text later
    // cocoa_set_accessibility_value_impl(text);
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
