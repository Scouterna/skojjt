$(document).ready(function() {
	$("#newmeeting").on('shown.bs.collapse', function (e) {
		$("#mname")[0].focus();
	});
	$("#newhike").on('shown.bs.collapse', function (e) {
		$("#mhikename")[0].focus();
	});

	$("#newmember").on('shown.bs.collapse', function (e) {
		$("#namesearch")[0].focus();
	});
	$(".attendance-cb").click(function(event) {
		meeting_url = event.target.name.slice(2);
		$('#btn'+meeting_url).css('background-color','#fa0');
	});
	$(".postattendance").click(function(event) {
		var button = event.target;
		if (button.type != "button") // if you press on the glyphicon inside the button
			button = event.target.parentNode; // get the parent button instead
			
		var meeting_url = button.id.slice(3);
		var checkboxes = $('input:checkbox[name="cb' + meeting_url + '"]');
		persons = '';
		for (var cb=0; cb < checkboxes.length; cb++)
		{
			if (persons.length > 0) persons += ',';
			if (checkboxes[cb].checked)
				persons += checkboxes[cb].id;
		}
		var fd = new FormData();
		fd.append("action", "saveattendance");
		fd.append("persons", persons);
		$('#btn'+meeting_url).css('background-color','#FFFF00');
		$.ajax({
			url:'./'+meeting_url+"/",
			data: fd,
			processData: false,
			contentType: false,
			type: 'POST',
			success: function(data) { if (data === "ok") $('#btn'+meeting_url).css('background-color','#00FF00');}
		});
	});
	$("#namesearch").on("keyup", function() {
		var val = $("#namesearch").val();
		if (val && val.length > 1)
		{
			$.ajax({
				url: '.',
				type: 'GET',
				data: 'action=lookupperson&name=' + val,
				async: true,
				success: function(data, textStatus, jqXHR) {
					arr = JSON.parse(data);
					t = "";
					$("#tblSearchResults").remove();
					table = $('<table id="tblSearchResults" class="table table-striped"/>');
					for (var x in arr)
					{
						table.append($('<tr><td><a href="' + arr[x].url + '?action=addperson">' + arr[x].name + '</a></td></tr>'));
					}
					$("#nameResults").append(table);
					return data;
				}
			})
		}
		else
		{
			$("#tblSearchResults").remove();
		}
	})		
});
