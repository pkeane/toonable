Toonable = {};


$(document).ready(function() {
	Toonable.initDelete();
	Toonable.setNow();
});

Toonable.setNow = function() {
    var target = document.getElementById('current');
    var d = new Date();
    var ts = d.getTime()/1000;
    target.innerHTML = d.toLocaleString();
}


Toonable.initDelete = function() {
	$('#todos').find("a[class='delete']").click(function() {
		if (confirm('are you sure?')) {
			var del_o = {
				'url': $(this).attr('href'),
				'type':'DELETE',
			'complete': function() { location.reload(); },
			};
			$.ajax(del_o);
		}
		return false;
	});
};
