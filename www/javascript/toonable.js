Tea = {};


$(document).ready(function() {
	Tea.initDelete();
});


Tea.initDelete = function() {
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
