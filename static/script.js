$(document).ready(function() {

    function json_post(url, data, success_callback) {
        $.ajax({
            url: url,
            type: "POST",
            data: JSON.stringify(data),
            contentType: "application/json",
            dataType: "json",
            success: success_callback,
        });
    };

    function SquashEvents(wait) {
        var timer = null;
        return function (event) {
            window.clearTimeout(timer);
            timer = window.setTimeout(event, wait);
        };
    };

    var volume_value = null; // used to prevent change event feedback loop
    var set_volume = SquashEvents(100);
    var url = $("#control_form").attr("action")

    function setup_main_page() {
        $.mobile.loading("show");
        $.get(url, {}, function (data) {
            var master_mute = $('#master_mute');
            var source = $('input[name=source]');
            if (data.master_mute !== undefined && data.master_mute !== null) {
                master_mute.val(data.master_mute);
                master_mute.slider("enable");
                master_mute.slider("refresh");
            }
            if (data.source !== undefined && data.source !== null) {
                var selector = "[value=" + data.source + "]";
                source.filter(selector).attr("checked", true);
                source.checkboxradio("enable");
                source.checkboxradio("refresh");
                setup_volume(data[data.source + "_volume"]);
            }
            $.mobile.loading("hide");
        }, "json");
    }

    function setup_volume(value) {
        var volume = $('#volume');
        volume_value = value;
        if (value !== undefined && value !== null) {
            volume.slider("enable");
            volume.val(value);
            volume.slider("refresh");
        } else {
            volume.val(0);
            volume.slider("refresh");
            volume.val(""); // clear numeric value
            volume.slider("disable");
        }
    }

    $('#main_page').on("pageshow", function (event, ui) {
        setup_main_page();
    });

    $('#master_mute').on("slidestop", function (event, ui) {
        json_post(url, {"master_mute": $(this).val()});
    });

    $('input[name=source]').change(function (event, ui) {
        var source_val = $(this).val();
        var data = {"source": source_val}
        var volume_key = source_val + "_volume"
        data[volume_key] = null; // request volume value in return data
        json_post(url, data, function (data) {
            setup_volume(data[volume_key]);
        });
    });

    $('#volume').change(function (event, ui) {
        var val = parseInt($(this).val());
        if (val === volume_value) return;
        volume_value = val;
        var source_val = $('input[name=source]:checked').val();
        var data = {};
        data[source_val + "_volume"] = val;
        set_volume(function () { json_post(url, data); });
    });

    function load_system_info(el) {
        $.mobile.loading("show");
        $.get("/system-info", {}, function (data) {
            $.mobile.loading("hide");
            $("#system_info").text(data);
        }, "text");
    };

    $('#info_page').on("pageshow", function (event, ui) {
        load_system_info();
    });

    $('#info_refresh').on("click", function (event, ui) {
        load_system_info();
        return false;
    });

    setup_main_page();
});
