const colors = [
    'rgb(255,99,99)',
    'rgb(255,171,118)',
    'rgb(255,253,162)',
    'rgb(186,255,180)'
];

var color_index = 0;

const base_config = {
    options : {
        animation : {
            duration : 250,
        },
    },
    type: 'line',
    data: {
        datasets: [
        ],
    }
};

var charts = [];

function Create_New_Chart_Config( data ) {
    var chart_conf = new Object();
    chart_conf["samples"] = data["samples"];
    chart_conf["id"] = data["id"];
    chart_conf["name"] = data["name"];
    chart_conf["fields"] = data["fields"];
    chart_conf["config"] = JSON.parse(JSON.stringify(base_config));

    var field_count = data["fields"].length;
    for ( var i=0; i<field_count; i++ ) {
        var line = new Object();
        line["data"] = [];
        line["label"] = (data["fields"][i]["device_name"].concat(" ")).concat(
            data["fields"][i]["name"]);
	line["backgroundColor"] = colors[color_index];
	line["borderColor"] = colors[color_index];
        chart_conf["config"]["data"]["datasets"].push(line);
        color_index = (color_index + 1) % 4;
        chart_conf["fields"][i]["data"] = line;
    }


    return chart_conf;
}

function Get_Devices_From_Chart_Config( chart_conf ) {
    var devices = [];

    var field_count = chart_conf["fields"].length;
    for ( var i=0; i<field_count; i++) {
        if (devices.includes(chart_conf["fields"][i]["id"]) != true ) {
            devices.push(chart_conf["fields"][i]["id"]);
        }
    }

    return devices;
}

function Get_Dataset_From_Device_And_Label( chart_conf, device_id, label ) {
    var field_count = chart_conf["fields"].length;

    for ( var i=0; i<field_count; i++ ) {
        if ( chart_conf["fields"][i]["id"] == device_id ) {
            if ( chart_conf["fields"][i]["name"] == label ) {
                return chart_conf["fields"][i]["data"];
            }
        }
    }

    return null;
}

async function Get_Data(device_id, samples) {
    var base_url = "/api/data/by_id/".concat(device_id);
    var parameters = "?limit=".concat(samples.toString());
    let response = await fetch(base_url.concat(parameters));
    let data = await response.json();
    return data;
}

function Transform_Data( data, label ) {
    var length = data[label].length;
    var items = [];
    for( var i=0; i<length; i++) {
        var item = new Object;
        item["x"] = data["timestamp"][i].toString();
        item["y"] = data[label][i];
        items.push(item);
    }
    
    return items;
}

window.onload = async() => {
    var url = "/api/dashboard"
    let response = await fetch(url);
    let data = await response.json();
    var length = data.length;

    for( var i=0; i<length; i++) {
        var chart_conf = Create_New_Chart_Config(data[i]);

        var canvas = Create_New_Chart(data[i]).getContext('2d');
        const chart = new Chart(canvas, chart_conf["config"]);

        chart_conf["chart"] = chart;

        charts.push(chart_conf);

    }

    var chart_count = charts.length;

    for( var i=0; i<chart_count; i++) {
        var chart_conf = charts[i];
        var field_count = chart_conf["fields"].length;
        for( var j=0; j<field_count; j++) {
            var field = chart_conf["fields"][j];
            var ddata = await Get_Data(field["id"], chart_conf["samples"]);
            if (field["name"] in ddata["data"]) {
                var items = Transform_Data( ddata["data"], field["name"]);
                field["data"]["data"] = items;
            }
        }
    }

    var chart_count = charts.length;
    for(var i=0; i<chart_count; i++) {
        charts[i]["chart"].update();
    }

    var webSocket = new WebSocket("ws://" + location.hostname + ":8338/client");


    webSocket.onmessage = function(event) {
        var msg = JSON.parse(event.data);
        var chart_count = charts.length;
        for(const property in msg) {
            for(var i=0; i<chart_count; i++) {
                var samples = charts[i]["samples"];
                var field_count = charts[i]["fields"];
                for(var j=0; j<field_count.length; j++) {
                    var field = charts[i]["fields"][j];
                    if (field["id"] == property) {
                        var ddata = msg[property];
                        if (field["name"] in ddata) {
                            var new_data = [];
                            var items = Transform_Data( ddata, field["name"]);
                            var item_length = items.length;
                            var curr_length = field["data"]["data"].length;
                            if (curr_length >= samples) {
                                if (item_length == samples) {
                                    new_data = items;
                                } else if (item_length > samples ) {
                                    var start = item_length - samples;
                                    new_data = items.splice(0, start);
                                } else {
                                    var diff = item_length;
                                    field["data"]["data"].splice(0, diff);
                                    var old_data = field["data"]["data"];
                                    new_data = old_data.concat(items);
                                }
                            } else {
                                if (item_length > samples ) {
                                    var start = item_length - samples;
                                    items.splice(0, start);
                                    new_data = items
                                } else {
                                    new_data = items;
                                }
                            }

                            field["data"]["data"] = new_data;
                            charts[i]["chart"].update();
                        }
                    }
                }
            }
        }
    }

    webSocket.onopen = function() {
        var chart_count = charts.length;
        var devices = [];
        for( var i=0; i<chart_count; i++ ) {
            var temp = Get_Devices_From_Chart_Config( charts[i] );
            devices = devices.concat(temp);
        }

        var devices_count = devices.length;
        for( var i=0; i<devices_count; i++) {
            var command_str = "ADD ";
            var command = command_str.concat(devices[i]);
            webSocket.send(command);
        }
    }
}

async function Remove_Chart(el) {
    var options = el.parentElement;
    var chart = options.parentElement;

    var canvas = chart.childNodes[0].childNodes[0];
    var id = canvas.id.substr(6);
   
    var url = '/api/dashboard/'.concat(id);
    let response = await fetch(url, {
        method: "DELETE",
        headers: {
            'Content-Type' : 'application/json'
        }
    });

    chart.remove();
    location.reload();
}

function Create_New_Chart(data) {
    var charts = document.getElementById('charts');

    var chart = document.createElement('div');
    chart.setAttribute("class", "chart");

    var chart_area = document.createElement('div');
    chart_area.setAttribute("class", "chart_area");

    var a_chart_area = document.createElement('canvas');
    a_chart_area.setAttribute("id", "canvas".concat(data["id"]));
    chart_area.appendChild(a_chart_area);

    var options = document.createElement('div');
    options.setAttribute("class", "chart_options");

    var option_button = document.createElement('button');
    option_button.setAttribute("onclick", "Remove_Chart(this)");
    var opt_button_text = document.createTextNode("Remove");
    option_button.appendChild(opt_button_text);

    options.appendChild(option_button);

    chart.appendChild(chart_area);
    chart.appendChild(options);

    charts.appendChild(chart);

    return a_chart_area;
}

function Create_Label(name, for_label) {
    var text = document.createTextNode(name);
    var bold = document.createElement("b");
    bold.appendChild(text);

    var label = document.createElement("label");
    label.setAttribute("for", for_label);

    label.appendChild(bold);

    return label;
}

function Make_Options(element, listindex) {
    var options = [].concat(device_opts[listindex]);
    var select = (element.parentElement).childNodes[4];

    while (select.childNodes.length > 0 ) {
        select.childNodes[0].remove();
    }

    for(var i=0; i<options.length; i++) {
        var opt = document.createElement("option");
        opt.setAttribute("value", options[i]);
        var opt_text = document.createTextNode(options[i]);
        opt.appendChild(opt_text);
        select.appendChild(opt);
    }
}

function Create_Dropdown( name, class_name, change, opt_names, opt_values) {
    var select = document.createElement("select");
    select.setAttribute("name", name);
    select.setAttribute("class", class_name);
    if(change == true) {
        select.setAttribute("onchange",
            "Make_Options(this, this.options[this.selectedIndex].value)");
    }

    var length = opt_names.length;
    for( var i=0; i<length; i++) {
        var opt = document.createElement("option");
        opt.setAttribute("value", opt_values[i]);
        var opt_text = document.createTextNode(opt_names[i]);
        opt.appendChild(opt_text);
        select.appendChild(opt);
    }

    return select;
}

function Create_Field(index, parent_tag, devices) {
    var container = document.createElement("div");
    container.setAttribute("class", "option_field");

    var index_label = Create_Label(index.toString(), "index");
    var device_label = Create_Label("device", "device");
    var device_opt_label = Create_Label("field", "device_options");

    var device = Create_Dropdown( "device", "device_choose", true, devices[0],
        devices[1]);

    var fields = device_opts[devices[1][0]];
    var device_opt = Create_Dropdown( "options", "opt_choose", false, fields, fields );

    var remove = document.createElement("button");
    remove.setAttribute("onclick", "Remove_Field(this)");
    var remove_text = document.createTextNode("Remove");
    remove.appendChild(remove_text);

    container.appendChild(index_label);
    container.appendChild(device_label);
    container.appendChild(device);
    container.appendChild(device_opt_label);
    container.appendChild(device_opt);
    container.appendChild(remove);

    parent_tag.appendChild(container);
}

function Remove_Field(element) {
    var field = element.parentElement;
    field.remove();
    index -= 1;
}

function New_Field(element) {
    var fields = document.getElementsByClassName('field_options')[0];
    Create_Field(index, fields, devices);
    index += 1;
}

function Cancel_New_Chart(element) {
    var div = element.parentElement;
    var form = div.parentElement;
    form.remove();
    index = 0;
}

var devices = [];
var device_opts = new Object;
var index = 0;

async function New_Chart() {
    index = 0;
    devices = [[],[]];
    device_opts =  new Object;

    var url = "/api/device";
    let response = await fetch(url);
    var data = await response.json();
    data = data["data"];
    for(var i=0; i<data.length; i++) {
        devices[0].push(data[i]["name"]);
        devices[1].push(data[i]["id"]);
        var device_url = "/api/device/by_id/".concat(data[i]["id"]);
        let new_response = await fetch(device_url);
        var dev_data = await new_response.json();
        var fields = dev_data["fields"];
        var labels = []
        for (var j=0; j<fields.length; j++) {
            labels.push(fields[j]["name"]);
        }
        device_opts[data[i]["id"]] = labels;
    }

    var area = document.getElementById('new_chart_area');

    var samples = Create_Label("Samples", "samples");

    var samples_field = document.createElement("input");
    samples_field.setAttribute("type", "number");
    samples_field.setAttribute("placeholder", "100");
    samples_field.setAttribute("name", "samples");
    samples_field.required = true;

    var div_container = document.createElement("div");
    var form = document.createElement("form");
    form.setAttribute("action", "");
    form.setAttribute("method", "post");
    form.setAttribute("id", "new_chart_form");

    div_container.appendChild(samples);
    div_container.appendChild(samples_field);

    fields = document.createElement("div");
    fields.setAttribute("class", "field_options");

    Create_Field( index, fields, devices );
    index += 1;

    var new_field_button = document.createElement("button");
    new_field_button.setAttribute("onclick", "New_Field(this)");
    var new_field_text = document.createTextNode("New field");
    new_field_button.appendChild(new_field_text);

    div_container.appendChild(new_field_button);
    div_container.appendChild(fields);

    var cancel_button = document.createElement("button");
    cancel_button.setAttribute("onclick", "Cancel_New_Chart(this)");
    var cancel_text = document.createTextNode("Cancel");
    cancel_button.appendChild(cancel_text);

    var submit_button = document.createElement("button");
    submit_button.setAttribute("type", "submit");
    var submit_text = document.createTextNode("Create Chart");
    submit_button.appendChild(submit_text);

    div_container.appendChild(submit_button);
    div_container.appendChild(cancel_button);

    form.appendChild(div_container);
    if( area.childNodes.length > 0 ) {
        for(var i=0; i<area.childNodes.length; i++) {
            area.childNodes[i].remove();
        }
    }

    area.appendChild(form);

    form.addEventListener('submit', async(event) => {
        event.preventDefault();

        var trans = new Object;
        trans["samples"] = form.elements["samples"].value
        trans["fields"] = [];
        var devs = [].concat(form.elements["device"]);
        var opts = [].concat(form.elements["options"]);
        for(var i=0; i<devs.length; i++) {
            var field = new Object;
            field["device_id"] = devs[i].value;
            field["name"] = opts[i].value;
            trans["fields"].push(field);
        }

        let response = await fetch("/api/dashboard", {
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

function Cancel_Download(element) {
    var parent = element.parentElement;
    var div = parent.parentElement;
    parent.remove();
    var form = document.createElement("form");
    form.setAttribute("id", "data_form");
    div.appendChild(form);
}

async function Create_Download_Field(element) {
    var div = element.parentElement;
    var form = null;
    for( var i = 0; i < div.childNodes.length; i++ ) {
        if ( div.childNodes[i].id == "data_form" ) {
            form = div.childNodes[i];
        }
    }
    if ( form == null ) {
        return null;
    } else {
        form.remove();
    }

    form = document.createElement("form");
    form.setAttribute("id", "data_form");
    div.appendChild(form);

    var url = "/api/device";
    let response = await fetch(url);
    var data = await response.json();
    data = data["data"];
    var devices = [];
    for(var i=0; i<data.length; i++) {
        devices.push(data[i]["name"]);
    }

    var label = Create_Label("Device", "device");
    var dropdown = Create_Dropdown("device", "device_choose", true, devices, devices);
    form.appendChild(label);
    form.appendChild(dropdown);
    var ok = document.createElement("button");
    var ok_text = document.createTextNode("OK");
    ok.setAttribute("type", "submit");
    ok.appendChild(ok_text);

    var cancel = document.createElement("button");
    var cancel_text = document.createTextNode("Cancel");
    cancel.setAttribute("onclick", "Cancel_Download(this)");
    cancel.setAttribute("type", "button");
    cancel.appendChild(cancel_text);

    form.appendChild(ok);
    form.appendChild(cancel);

    form.addEventListener('submit', async event => {
        event.preventDefault();
        var device = form.elements["device"][0].value;

        const a = document.createElement('a');
        a.href = "/download/device/by_name/".concat(device);
        a.download = url.split('/').pop();
        a.setAttribute("download", "true");
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        form.remove()
    });

    return null;
}
