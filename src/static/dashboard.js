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
var devices = [];

function Create_New_Chart_Config( data ) {
    var chart_conf = new Object();
    chart_conf["samples"] = data["samples"];
    chart_conf["id"] = data["id"];
    chart_conf["name"] = data["name"];
    chart_conf["fields"] = data["fields"];
    chart_conf["config"] = base_config;

    var field_count = data["fields"].length;
    for ( var i=0; i<field_count; i++ ) {
        var line = new Object();
        line["data"] = [];
        line["label"] = (data["fields"][i]["device_name"].concat(" ")).concat(
            data["fields"][i]["name"]);
        chart_conf["config"]["data"]["datasets"].push(line);
        chart_conf["fields"][i]["data"] = line;
    }

    return chart_conf;
}

function Get_Devices_From_Chart_Config( chart_conf ) {
    var devices = [];

    var field_count = chart_conf["fields"].length;
    for ( var i=0; i<field_count; i++) {
        if (devices.includes(chart_conf["fields"][i]["id"]) != true ) {
            console.log(chart_conf["fields"][i]["id"]);
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
                var length = ddata["data"][field["name"]].length;
                for( var z=0; z<length; z++) {
                    var item = new Object;
                    item["x"] = ddata["data"]["timestamp"][z].toString();
                    item["y"] = ddata["data"][field["name"]][z];
                    field["data"]["data"].push(item);
                }
            }
        }
    }

    var chart_count = charts.length;
    for(var i=0; i<chart_count; i++) {
        charts[i]["chart"].update();
    }

    var webSocket = new WebSocket("ws://127.0.0.1:8338/client");


    webSocket.onmessage = function(event) {
        var msg = JSON.parse(event.data);
        console.log(msg);
        var chart_count = charts.length;
        for(const property in msg) {
            for(var i=0; i<chart_count; i++) {
                var samples = charts[i]["samples"];
                var field_count = charts[i]["fields"];
                for(var j=0; j<chart_count; j++) {
                    var field = charts[i]["fields"][j];
                    if (field["id"] == property) {
                        var ddata = msg[property];
                        if (field["name"] in ddata["data"]) {
                            var length = ddata["data"][field["name"]].length;
                            for( var z=0; z<length; z++) {
                                var item = new Object;
                                item["x"] = ddata["timestamps"][z].toString();
                                item["y"] = ddata["data"][field["name"]][z];
                                field["data"]["data"].push(item);
                            }
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
            console.log(command);
            webSocket.send(command);
        }
    }
}

function Create_New_Chart(data) {
    var charts = document.getElementById('charts');

    var chart = document.createElement('div');
    chart.setAttribute("class", "chart");

    var chart_area = document.createElement('div');
    chart_area.setAttribute("class", "chart_area");

    var a_chart_area = document.createElement('canvas');
    a_chart_area.setAttribute("id", data["id"]);
    chart_area.appendChild(a_chart_area);

    var options = document.createElement('div');
    options.setAttribute("class", "chart_options");

    var option_button = document.createElement('button');
    option_button.setAttribute("onclick", "Remove_Chart()");
    var opt_button_text = document.createTextNode("Remove");
    option_button.appendChild(opt_button_text);

    options.appendChild(option_button);

    chart.appendChild(chart_area);
    chart.appendChild(options);

    charts.appendChild(chart);

    return a_chart_area;
}

function New_Chart() {
    var area = document.getElementById('new_chart_area');

    var samples = document.createElement("label");
    samples.setAttribute("for", "samples");

    var samples_b = document.createElement("b");
    var samples_text = document.createTextNode("Samples");
    samples_b.appendChild(samples_text)
    samples.appendChild(samples_b);

    var samples_field = document.createElement("input");
    samples_field.setAttribute("type", "number");
    samples_field.setAttribute("placeholder", "100");
    samples_field.required = true;

    var div_container = document.createElement("div");
    var form = document.createElement("form");
    form.setAttribute("action", "");
    form.setAttribute("method", "post");

    div_container.appendChild(samples);
    div_container.appendChild(samples_field);

    form.appendChild(div_container);

    area.appendChild(form);
}
