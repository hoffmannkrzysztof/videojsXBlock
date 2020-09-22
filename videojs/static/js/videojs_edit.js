/* Javascript for videojsXBlock. */
function videojsXBlockInitStudio(runtime, element) {

    $(element).find('.action-cancel').bind('click', function () {
        runtime.notify('cancel', {});
    });

    $(element).find('.action-save').bind('click', function () {
        var data = {
            'display_name': $('#videojs_edit_display_name').val(),
            'url': $('#videojs_edit_url').val(),
        };

        $(".subtitle_text").each(function (index) {
            data['subtitle_text_' + $(this).attr("data-language")] = $(this).val();
        });

        console.log(data);

        runtime.notify('save', {state: 'start'});

        var handlerUrl = runtime.handlerUrl(element, 'save_videojs');
        $.post(handlerUrl, JSON.stringify(data)).done(function (response) {
            if (response.result === 'success') {
                runtime.notify('save', {state: 'end'});
                // Reload the whole page :
                // window.location.reload(false);
            } else {
                runtime.notify('error', {msg: response.message})
            }
        });
    });
}
