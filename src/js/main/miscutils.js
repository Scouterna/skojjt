function getTodaysDateString()
{
	var today = new Date();
	var dd = ("0" + (today.getDate())).slice(-2);
	var mm = ("0" + (today.getMonth() + 1)).slice(-2);
	var yyyy = today.getFullYear();
	today = yyyy + '-' + mm + '-' + dd ;
	return today;
}
function getCurrentHalfHourString()
{
	var today = new Date();
	var h = today.getHours();
	var m = today.getMinutes();
	var frac = Math.round(m/60*2.0)/2.0;
	m = (frac * 60) % 60;
	if (frac > 0.5)
	{
		h += 1;
		h %= 24;
	}
	var hh = ("0" + h).slice(-2);
	var mm = ("0" + m).slice(-2);
	timestr = hh + ':' + mm;
	return timestr;
}
function postWithParams(path, params, method) 
{
	method = method || "post";
	var form = document.createElement("form");
	form.setAttribute("method", method);
	form.setAttribute("action", path);

	for(var key in params) 
	{
		if (params.hasOwnProperty(key))
		{
			var hiddenField = document.createElement("input");
			hiddenField.setAttribute("type", "hidden");
			hiddenField.setAttribute("name", key);
			hiddenField.setAttribute("value", params[key]);
			form.appendChild(hiddenField);
		 }
	}
	document.body.appendChild(form);
	form.submit();
}

function postData(absolutePath, data, onsuccess, onfailure)
{
	var XHR = new XMLHttpRequest();
	var urlEncodedData = "";
	var urlEncodedDataPairs = [];
	var name;

	// We turn the data object into an array of URL encoded key value pairs.
	for(name in data) 
	{
		urlEncodedDataPairs.push(encodeURIComponent(name) + '=' + encodeURIComponent(data[name]));
	}

	// We combine the pairs into a single string and replace all encoded spaces to 
	// the plus character to match the behaviour of the web browser form submit.
	urlEncodedData = urlEncodedDataPairs.join('&').replace(/%20/g, '+');

	// We define what will happen if the data is successfully sent
	XHR.addEventListener('load', function(event) 
	{
		if (onsuccess) onsuccess();
	});

	// We define what will happen in case of error
	XHR.addEventListener('error', function(event) 
	{
		if (onfailure) onfailure();
	});

	// We setup our request
	XHR.open('POST', absolutePath);

	// We add the required HTTP header to handle a form data POST request
	XHR.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
	// XHR.setRequestHeader('Content-Length', urlEncodedData.length);

	// And finally, We send our data.
	XHR.send(urlEncodedData);
}	

function postCheckboxesWithName(path, name, onsuccess, onfailure)
{
	var elem = document.getElementsByName(name);
	var persons = new Array()
	for (var i=0; i < elem.length; i++)
	{
		if (elem[i].checked)
			persons.push(elem[i].id);
	}
	var absolutePath = window.location.href;
	var lastChar = absolutePath.substr(-1);
	if (lastChar !== '/')
	{
		absolutePath = absolutePath + '/';
	}
	if (lastChar !== '?')
	{
		absolutePath = absolutePath.substr(absolutePath.length);
	}
	absolutePath = absolutePath + path;
	postData(absolutePath, {meeting:name.slice(2), persons:persons}, onsuccess, onfailure);
}
