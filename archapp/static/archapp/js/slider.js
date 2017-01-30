(function(jQuery) {
    $(document).ready(function($){
        var d = $('#id_dating');

        if( d.length )
        {
            var l = $("<span id = 'slider_label'>aewoeirn908</span>")
            var z = $("<div id = 'slider'></div>");
            var q = function(a, b) {
                $('#id_datingfrom').val(a);
                $('#id_datingto').val(b); }
            var x = function(e, ui) {
                var r1 = d.find('option').eq(ui.values[0] - 1);
                var r2 = d.find('option').eq(ui.values[1] - 1);
                q(r1[0].value, r2[0].value);
                l.html(r1.text() + ' - ' + r2.text()); }
            var s = z.slider({
                min: 1,
                max: 16,
                range: true,
                values: [d[0].selectedIndex, d[0].selectedIndex ],
                slide: x });
            $('#id_undefined').click(function(){
                if ($(this).is(':checked'))
                {
                    z.slider('option', 'disabled', true);
                    q(-1, -1);
                    l.html('---');
                }
                else
                {
                    z.slider('option', 'disabled', false);
                    z.trigger('slidechange');
                    x(null, z.slider("instance").options);
                }
            });

            d.hide();
            d.after(l);
            l.after(z);
            var def_val1 = 3;
            var def_val2 = 6;
            if (typeof $('#id_datingfrom').val() !== 'undefined') {
            var df = $('#id_datingfrom').val(); 
            var dt = $('#id_datingto').val();
            var count = 0;
            $.each($('#id_dating option'), function(i, opt){
              if ($(opt).attr('value') == df) {
               def_val1 = i+1; 
              };
              if ($(opt).attr('value') == dt) {
               def_val2 = i+1; 
              };

            }); 
            }; 
            z.slider('values', [def_val1, def_val2]);
            x(null, z.slider("instance").options);
        }

    });
})()
