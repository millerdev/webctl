$(document).ready(function() {

    function json_post(url, data) {
        $.ajax({
            url: url,
            type: "POST",
            data: JSON.stringify(data),
            contentType: "application/json",
            dataType: "json",
        });
    };

    function SquashEvents(wait) {
        var timer = null;
        return function (event) {
            window.clearTimeout(timer);
            timer = window.setTimeout(event, wait);
        };
    };

    // used to prevent change event feedback loop
    var sound_src_value = null;
    var tv_volume_value = null;
    var sp_volume_value = null;

    var set_volume = SquashEvents(100);
    var url = $("#control_form").attr("action")

    function setup_main_page() {
        $.mobile.loading("show");
        $.get(url, {}, function (data) {
            var master_mute = $('#master_mute');
            var sound_source = $('input[name=sound_source]');
            var tv_vol = $('#tv_vol');
            var sp_vol = $('#airpogo_vol');
            if (data.master_mute !== undefined && data.master_mute !== null) {
                master_mute.val(data.master_mute);
                master_mute.slider("enable");
                master_mute.slider("refresh");
            }
            sound_src_value = data.sound_source
            if (data.sound_source !== undefined && data.sound_source !== null) {
                var selector = "[value=" + data.sound_source + "]";
                sound_source.filter(selector).attr("checked", true);
                sound_source.checkboxradio("enable");
                sound_source.checkboxradio("refresh");
            }
            tv_volume_value = data.tv_volume;
            if (data.tv_volume !== undefined && data.tv_volume !== null) {
                tv_vol.val(data.tv_volume);
                tv_vol.slider("enable");
                tv_vol.slider("refresh");
            }
            sp_volume_value = data.airpogo_volume;
            if (data.airpogo_volume !== undefined
                    && data.airpogo_volume !== null) {
                sp_vol.val(data.airpogo_volume);
                sp_vol.slider("enable");
                sp_vol.slider("refresh");
            }
            $.mobile.loading("hide");
        }, "json");
    };
    setup_main_page();

    $('#main_page').on("pageshow", function (event, ui) {
        setup_main_page();
    });

    $('#master_mute').on("slidestop", function (event, ui) {
        json_post(url, {"master_mute": $(this).val()});
    });

    $('input[name=sound_source]').change(function (event, ui) {
        json_post(url, {"sound_source": $(this).val()});
    });

    $('#tv_vol').change(function (event, ui) {
        var val = parseInt($(this).val());
        if (val === tv_volume_value) return;
        tv_volume_value = val;
        set_volume(function () {
            json_post(url, {"tv_volume": val});
        });
    });

    $('#airpogo_vol').change(function (event, ui) {
        var val = parseInt($(this).val());
        if (val === sp_volume_value) return;
        sp_volume_value = val;
        set_volume(function () {
            json_post(url, {"airpogo_volume": val});
        });
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

});
