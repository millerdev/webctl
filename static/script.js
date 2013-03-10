$(document).ready(function() {

    function json_post(url, data, success) {
        $.ajax({
            url: url,
            type: "POST",
            data: JSON.stringify(data),
            contentType: "application/json",
            dataType: "json",
            success: success
        });
    };

    function SquashEvents(wait) {
        var timer = null;
        return function (event) {
            window.clearTimeout(timer);
            timer = window.setTimeout(event, wait);
        };
    };

    var tv_volume_value = null; // used to prevent change event feedback loop
    var set_volume = SquashEvents(100);
    var url = $("#tv_volume_form").attr("action")

    $.get(url, {}, function (data) {
        var tv_toggle = $('#tv_toggle');
        var tv_vol = $('#tv_vol');
        if (data.loopback !== undefined) {
            tv_toggle.val(data.loopback);
        }
        tv_volume_value = data.volume;
        if (data.volume !== undefined) {
            tv_vol.val(data.volume);
        }
        tv_vol.slider("enable");
        tv_toggle.slider("enable");
        tv_vol.slider("refresh");
        tv_toggle.slider("refresh");
    }, "json");

    $('#tv_vol').change(function (event, ui) {
        var val = parseInt($(this).val());
        if (val === tv_volume_value) return;
        tv_volume_value = val;
        set_volume(function () {
            json_post(url, {"volume": val}, function (data) {
                if (data.loopback !== undefined) {
                    $('#tv_toggle').val(data.loopback);
                }
            }, "json");
        });
    });

    $('#tv_toggle').on("slidestop", function (event, ui) {
        var slider = $('#tv_toggle');
        json_post(url, {"loopback": $(this).val()}, function (data) {
            if (data.loopback !== undefined) {
                slider.val(data.loopback);
            }
        }, "json");
    });

});
