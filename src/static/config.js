async function Get_Devices() {
    var url = "/api/device";
    let response = await fetch(url);
    let data = await response.json();
    return data["data"];
}

async function Get_Device_Info(device_id) {
    var url = "/api/device/by_id/".concat(device_id);
    let response = await fetch(url);
    let data = await response.json();
    return data;
}

function Create_Field(label, value) {
    var li = document.createElement('li');
    var label_span = document.createElement('span');
    var label_text = document.createTextNode(label);
    label_span.appendChild(label_text);

    var value_span = document.createElement('span');
    var value_text = document.createTextNode(value);
    value_span.appendChild(value_text);

    var sep_span = document.createElement("span");
    var sep_text = document.createTextNode(":");
    sep_span.appendChild(sep_text);

    li.appendChild(label_span);
    li.appendChild(sep_span);
    li.appendChild(value_span);

    return li;
}

async function Delete_Device(element) {
    var container = element.parentElement;

    var container_id = container.id;

    var device_id = container_id.substr(7);

    var url = "/api/device/by_id/".concat(device_id);
    let response = await fetch(url, {
        method: "DELETE",
        headers : {
            'Content-Type' : 'application/json'
        }
    })

    location.reload();
}

function Create_Device_Field(device) {
    var dev = document.createElement('div');
    dev.setAttribute('class', 'device');
    dev.setAttribute('id', 'device_'.concat(device["id"]));

    var delete_btn = document.createElement("button");
    delete_btn.setAttribute("onclick", "Delete_Device(this)");
    var delete_btn_text = document.createTextNode("Delete");
    delete_btn.appendChild(delete_btn_text);

    var list = document.createElement('ul');

    var key = Create_Field("device key", device["id"]);
    var name = Create_Field("device name", device["name"]);

    list.appendChild(key);
    list.appendChild(name);

    dev.appendChild(list);
    dev.appendChild(delete_btn);

    return dev;
}

window.onload = async() => {

    const base = document.getElementById("devices");

    var devices = await Get_Devices();

    var devices_info = [];
    for(var i=0; i<devices.length; i++) {
        var device = await Get_Device_Info(devices[i]["id"]);
        devices_info.push(device);
    }

    for(var i=0; i<devices_info.length; i++) {
        var device_field = Create_Device_Field(devices_info[i]);
        base.appendChild(device_field);
    }
};

function Create_Label(label_name, for_name) {
    var label = document.createElement("label");
    label.setAttribute("name", label_name);
    label.setAttribute("for", for_name);
    
    var bold = document.createElement("b");
    var bold_text = document.createTextNode(label_name);
    bold.appendChild(bold_text);

    label.appendChild(bold);

    return label;
}

function New_Option_Field(element) {
    var container = document.createElement("div");
    container.setAttribute("class", "field");
    var select = document.createElement("select");
    select.setAttribute("name", "Type");
    select.setAttribute("class", "choose_Type");

    var float_opt = document.createElement("option");
    float_opt.setAttribute("value", "float");
    var float_opt_text = document.createTextNode("float");
    float_opt.appendChild(float_opt_text);

    var int_opt = document.createElement("option");
    int_opt.setAttribute("value", "int");
    var int_opt_text = document.createTextNode("int");
    int_opt.appendChild(int_opt_text);

    select.appendChild(float_opt);
    select.appendChild(int_opt);

    var label = Create_Label("Field Name", "field_name");
    var samples_field = document.createElement("input");
    samples_field.setAttribute("type", "text");
    samples_field.setAttribute("placeholder", "field name");
    samples_field.setAttribute("name", "field_name");
    samples_field.required = true;

    var remove_btn = document.createElement("button");
    remove_btn.setAttribute("onclick", "Remove_Specific_Field(this)");
    var remove_btn_text = document.createTextNode("remove");
    remove_btn.appendChild(remove_btn_text);

    container.appendChild(select);
    container.appendChild(label);
    container.appendChild(samples_field);
    container.appendChild(remove_btn);

    var up = element.parentElement;
    up.appendChild(container);
}

function Remove_Specific_Field(element) {
    var up = element.parentElement;
    up.remove();
}

async function Create_New_Device() {
    var container = document.createElement("div");

    var create = document.createElement("button");
    create.setAttribute("type", "submit");
    var create_text = document.createTextNode("Create Device");
    create.appendChild(create_text);

    var cancel = document.createElement("button");
    cancel.setAttribute("onclick", "Cancel_New_Device()");
    var cancel_text = document.createTextNode("Cancel");
    cancel.appendChild(cancel_text);

    var form = document.createElement("form");
    form.setAttribute("id", "new_device_form");
    form.setAttribute("action", "");
    form.setAttribute("method", "post");

    var div_container = document.createElement("div");

    var name_label = Create_Label("Name", "name");
    var name_field = document.createElement("input");
    name_field.setAttribute("type", "text");
    name_field.setAttribute("placeholder", "name");
    name_field.setAttribute("name", "name");
    name_field.required = true;

    var new_field = document.createElement("button");
    new_field.setAttribute("onclick", "New_Option_Field(this)");
    var new_field_text = document.createTextNode("New Field");
    new_field.appendChild(new_field_text);

    var field_container = document.createElement("div");
    field_container.appendChild(new_field);

    div_container.appendChild(name_label);
    div_container.appendChild(name_field);
    div_container.appendChild(field_container);
    div_container.appendChild(create);
    div_container.appendChild(cancel);

    form.appendChild(div_container);

    var new_device_div = document.getElementById('new_device_div');
    if( new_device_div.childNodes.length > 0 ) {
        for( var i=0; i<new_device_div.childNodes.length; i++) {
            new_device_div.childNodes[i].remove();
        }
    }

    new_device_div.appendChild(form);

    form.addEventListener('submit', async(event) => {
        event.preventDefault();

        var trans = new Object;
        trans["name"] = form.elements["name"].value;
        trans["fields"] = [];
        var types = Array.from(form.elements["Type"]);
        if(types.length == 0) {
            types.push(form.elements["Type"]);
        }
        var names = Array.from(form.elements["field_name"]);
        if(names.length == 0) {
            names.push(form.elements["field_name"]);
        }

        for(var i=0; i<names.length; i++ ) {
            var field = new Object;
            field["type"] = types[i].value;
            field["name"] = names[i].value;
            trans["fields"].push(field);
        }

        let response = await fetch("/api/device", {
            method: "POST",
            body: JSON.stringify(trans),
            headers: {
                "Content-Type" : "application/json"
            }
        });

        form.remove();
        location.reload();

    });
}

function Cancel_New_Device() {
    var container = document.getElementById("new_device_div");
    var list = container.childNodes;

    for(var i=0; i<list.length; i++ ) {
        list[i].remove();
    }
}
