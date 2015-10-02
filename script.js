// setup webiopi ready func
webiopi().ready(init);

// init function called when webiopi js library is ready
function init() {
    
    // Set mode button onClick listener
    $("#mode").bind("click", toggleMode);
    
    // Get startHour <select> HTML/jQuery object
    startHour = $("#startHour");
    // Set onChange listener
    startHour.bind("change", setStart);
    // Append 0-23 options
    for (h=0; h<24; h++) {
        if (h < 10) {
            h = "0" + h;
        }
        startHour.append($("<option>" + h + "</option>"));
    }
    
    // Get startMinute <select>
    startMinute = $("#startMinute");
    // Set onChange listener
    startMinute.bind("change", setStart);
    // Append 0-59 options
    for (m=0; m<60; m++) {
        if (m < 10) {
            m = "0" + m;
        }
        startMinute.append($("<option>" + m + "</option>"));
    }
    
    // Iterate over days buttons
    for (j=0; j<7; j++) {
        // Get button
        button = $("#day-"+j);
        // Set onClick listener
        button.bind("click", dayClick);
    }
    
    // Iterate over channels
    for (var c=0; c<16; c++) {
        // Get channel button
        button = $("#channel-"+c);
        // Set onClick listener
        button.bind("click", channelClick);

        // Get channel slider
        slider = $("#slider-"+c);
        // Set onChange listener
        slider.bind("change", sliderChange);
    }
    

    // Update UI now...
    updateUI();

    // ...then each seconds
    setInterval(updateUI, 1000);
}

/****************************************/
/* functions and callbacks to update UI */
/****************************************/

// Called in init() then by setInteval()
function updateUI() {
    // call getAll macro
    webiopi().callMacro("getAll", [], getAllCallback);
}

// callback used by getAll macro
function getAllCallback(macro, args, data) {
    // parse json received
    json = JSON.parse(data);
    // update mode button
    updateMode(json["mode"]);
    // update start time
    updateStart(json["start"]);
    // update schedule
    updateDays(json["days"]);
    // update channels buttons
    updateChannels(json["channels"]);
    // update channels sliders
    updateSliders(json["durations"]);
}

// update mode button
function updateMode(mode) {
    // Set mode button text
    $("#mode").text(mode);
    // Set appropriate CSS class
    if (mode == "auto") {
        $("#mode").attr("class", "ENABLED")
    }
    else {
        $("#mode").attr("class", "DISABLED")
    }
}

// update start time
function updateStart(start) {
    var time = start.split(":");
    $("#startHour").val(time[0]);
    $("#startMinute").val(time[1]);
}

// update all days schedule
function updateDays(data) {
    // Iterate over array
    for (day in data) {
        updateDay(day, data[day]);
    }
}

// update a single day schedule
function updateDay(day, enabled) {
    // Get corresponding button
    button = $("#day-" + day)
    // Update UI
    if (enabled == 0) {
        button.text("OFF");
        button.attr("class", "DISABLED")
    }
    else {
        button.text("ON");
        button.attr("class", "ENABLED")
    }
}

// Callback function used by mcp.readAll to update UI
function updateChannels(data) {
    // iterate over array
    for (channel in data) {
        // update each channel button
        updateChannel(channel, data[channel]);
    }
}
 
// update a single channel
function updateChannel(channel, value) {
    // Get channel button
    button = $("#channel-" + channel);
    // Test result and update UI
    if (value == 1) {
        button.text("ON");
        button.attr("class", "ENABLED")
    }
    else if (value == 0) {
        button.text("OFF");
        button.attr("class", "DISABLED")
    }
    // -1 means channel is Waiting for previous channel finish
    else if (value == -1) {
        button.text("W");
        button.attr("class", "WAITING")
    }
    
}

// update all sliders
function updateSliders(data) {
    for (channel in data) {
        updateSlider(channel, data[channel]);
    }
}

// update a single channel
function updateSlider(channel, value) {
    // Get channel value label and slider
    label = $("#label-" + channel);
    slider = $("#slider-" + channel);
    // Set label and slider value
    label.text(value + " mins");
    slider.val(value);
}




/***********************************************************/
/* Buttons and controls listeners, callbacks and functions */
/***********************************************************/

// called by the mode button
function toggleMode() {
    // test current mode
    if ($("#mode").text() == "auto") {
        // call setMode macro with "manual" argument
        webiopi().callMacro("setMode", "manual", setModeCallback);
    }
    else if ($("#mode").text() == "manual") {
        // call setMode macro with "auto" argument
        webiopi().callMacro("setMode", "auto", setModeCallback);
    }
}

// callback used by setMode macro to display current mode
function setModeCallback(macroName, args, data) {
    // updaze mode button
    updateMode(data);
}

// start drop-menus onChange listener
function setStart() {
    // Get UI values
    hour = $("#startHour").val();
    minute = $("#startMinute").val();
    // Call setStart macro with given arguments
    webiopi().callMacro("setStart", [hour, minute])
}

// days buttons onClick listener
function dayClick() {
    // Retrieve clicked button
    button = $(this);
    // Get day from button ID
    day = button.attr("id").split("-")[1];
    // Test current button state
    if (button.text() == "ON") {
        // Day currently ON, turning it OFF
        webiopi().callMacro("setDay", [day, 0], setDayCallback);
    }
    else {
        // Else day is certainly OFF, turning it ON
        webiopi().callMacro("setDay", [day, 1], setDayCallback);
    }
}

// callback used by setDay macro to update UI
// actually call getDayCallback
function setDayCallback(macro, args, response) {
    // setDay takes 2 arguments
    var day = args[0];
    // getDay takes only one argumen
    updateDay(parseInt(day), parseInt(response));
}

// slider onChange listener
function sliderChange() {
    // Get changed slider
    slider = $(this);
    // Get channel from slider ID
    channel = slider.attr("id").split("-")[1];
    // Get new slider value
    value = slider.val();
    // Get channel value label
    label = $("#label-"+channel);
    // Update channel value label
    label.text(slider.val() + " mins");
    // Change channel value label background while updating
    label.css("background-color", "grey");
    // Call setDuration macro with the given channel and value
    webiopi().callMacro("setDuration", [channel, value], setDurationCallback);
    
}

// callback used by setDuration macro to udpate UI
function setDurationCallback(macro, args, response) {
    // setDuration take 2 arguments
    channel = args[0];
    // Get channel value label
    label = $("#label-" + channel);
    // Update channel value label
    label.text(response + " mins");
    // Reset background color
    label.css("background-color", "transparent");

}

// channels button onClick listener
function channelClick() {
    // Retrieve button
    button = $(this);
    // Retrieve channel from button ID
    channel = button.attr("id").split("-")[1];

    // retuns if mode is auto to forbids changes
    if ($("#mode").text() == "auto") {
        return;
    }

    // Channel 0 is master channel
    if (channel == 0) {
        // Call switchMaster macro with appropriate value
        if (button.text() == "OFF") {
            webiopi().callMacro("switchMaster", 1, switchMasterCallback);
        }
        else {
            webiopi().callMacro("switchMaster", 0, switchMasterCallback);
        }
    }
    // Other channels
    else {
        // Call switchChannel macro with appropriate value
        if (button.text() == "OFF") {
            webiopi().callMacro("switchChannel", [channel, 1], switchChannelCallback);
        }
        else {
            webiopi().callMacro("switchChannel", [channel, 0], switchChannelCallback);
        }
    }
}

// callback used by switchMaster macro
function switchMasterCallback(name, value, response) {
    // update master button
    updateChannel(0, parseInt(response));
}

// callback used by switchChannel macro
function switchChannelCallback(name, args, response) {
    channel = args[0];
    value = parseInt(response);
    // update channel button
    updateChannel(channel, value);
}

