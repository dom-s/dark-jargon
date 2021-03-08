'use strict';

function getColor(label) {
	if (!label) {
		return (0, 0, 0);
	}
	let ret = [0, 0, 0],
		i = 0;
	for (i = 0; i < Math.min(label.length, 3); i++) {
		ret[i] = ((label.charCodeAt(i) * 49) % 255).toString();
	}
	return ret;
}

function getUnit(number) {
	if (number > 1e12) {
		return ["Trillion", 1e12];
	} else if (number > 1e9) {
		return ["Billion", 1e9];
	} else if (number > 1e6) {
		return ["Million", 1e6];
	} else if (number > 1e3) {
		return ["Tousand", 1e3];
	} else {
		return ["Unit", 1];
	}
}

function getSample(arr) {
	let i = 0,
		j = 0,
		max = 0;
	for (i = arr.length - 1; i > 0; i--) {
		for (j = arr[i].length - 1; j > 0; j--) {
			if (arr[i][j] && arr[i][j] > max) {
				max = arr[i][j];
			}
		}
	}
	return max;
}


function makeChart(chart_elem, years, dataset, country) {
	let ctx = chart_elem.getContext('2d');
	ctx.canvas.width = 1000;
	ctx.canvas.height = 375;
	let sample = getSample(dataset);
	let unit = getUnit(sample);
	let cfg = {
		type: 'bar',
		data: {
			labels: years,
			datasets: []
		},
		options: {
			scales: {
				yAxes: [{
					scaleLabel: {
						display: true,
						labelString: `Value (${unit[0]})`
					}
				}]
			},
			tooltips: {
				mode: 'nearest',
			}
		}
	};

	dataset.forEach(function (data) {
		let label = data[0] + '(' + country[data[0]] + ')';
		data.shift();
		let colors = getColor(label);
		let d = {
			label: label,
			data: data.map(function (x) { return x / unit[1] }),
			backgroundColor: `rgba(${colors[0]}, ${colors[1]}, ${colors[2]}, 0.6)`,
			borderColor: `rgba(${colors[0]}, ${colors[1]}, ${colors[2]}, 1)`,
			type: 'line',
			pointRadius: 1.6,
			fill: false,
			lineTension: 0,
			borderWidth: 2
		};
		cfg.data.datasets.push(d);
	});
	return new Chart(ctx, cfg);
}

function updateChart(url) {
	return function (e) {
		let data = {};
		data.year_from = $("#edstats-year-from").val();
		data.year_to = $("#edstats-year-to").val();
		data.indicator_name = $("#edstats-indicator-name").val() || $("#edstats-indicator-name-existed").text();
		$.ajax({
			method: 'POST',
			url: url,
			data: data,
		}).done(updateChartContent)
			.fail(function (XMLHttpRequest, textStatus, errorThrown) {
				console.log(XMLHttpRequest, textStatus, errorThrown);
			});
	}
}
function updateChartContent(res) {
	res = res.data;
	if (!res.data) {
		return;
	}
	$("#edstats-indicator-name-existed").text(res.indicator_name);
	let type = $('input[name=edstats-form-type]:checked', "#edstats-options").val();
	let i = 0;
	if (edStat_chart.config.data.datasets.length !== res.data.length) {
		edStat_chart.config.data.datasets = [];
	}

	let sample = getSample(res.data);
	let unit = getUnit(sample);
	for (i = 0; i < res.data.length; i++) {
		let data = res.data[i]
		let label = data[0] + '(' + res.country[data[0]] + ')';
		data.shift();
		edStat_chart.config.data.datasets[i].data = data.map(function (x) { return x / unit[1] });
		edStat_chart.config.data.datasets[i].label = label;
		edStat_chart.config.data.datasets[i].type = type;
		edStat_chart.config.options.scales.yAxes[0].scaleLabel.labelString = `Value (${unit[0]})`;
	};
	edStat_chart.config.data.labels = res.years;
	edStat_chart.update();
}

function expandIndexList(elem, indicator_name_url) {
	let data_loaded = $($(elem).attr('data-target')).attr('data-loaded');
	if (data_loaded) { return; }
	let data = {};
	data.path = [$(elem).text().trim()];
	$.ajax({
		method: 'POST',
		url: indicator_name_url,
		data: data,
	}).done(function (res) { expandIndexListContent(res, data) })
		.fail(function (XMLHttpRequest, textStatus, errorThrown) {
			console.log(XMLHttpRequest, textStatus, errorThrown);
		});
}

function expandIndexListContent(res, data) {
	if (!res.data) {
		return;
	}
	let i = 0;
	let is_leave = res.is_leave;
	let arr = res.data;
	if (is_leave) {
		for (i = 0; i < arr.length; i++) {
			let $newElem = $("<div>", { "html": arr[i], "class": "ml-5"}),
				$hr = $("<div>", { "class": "border-top my-3" });
			let card_id = '#' + data.path[0].replace(/[^a-zA-Z0-9]/g, '-');
			$(card_id).attr('data-loaded', true);
			$newElem.on('click', function(){
				$('#edstats-indicator-name').val($(this).text());
			})
			$newElem.appendTo($(card_id).find("div")[0]);
			if (i < arr.length - 1) { $hr.appendTo($(card_id).find("div")[0]); }
		}
	} else {
		// < !--Can add logic to multi - level expansion, didn't implement because lack of time -->
	}
}

function closeDropDown() {
	$(".autocomplete-item").remove();
}

function updateSearchDropdown(autocomplete_url) {
	return function (e) {
		e.preventDefault();
		let data = { indicator_name: $("#edstats-indicator-name").val() };
		if (!data['indicator_name']) {
			closeDropDown();
			return;
		}
		$.ajax({
			method: 'POST',
			url: autocomplete_url,
			data: data,
		}).done(updateSearchDropdownContent)
			.fail(function (XMLHttpRequest, textStatus, errorThrown) {
				console.log(XMLHttpRequest, textStatus, errorThrown);
			});
	}
}

function updateSearchDropdownContent(res) {
	closeDropDown();
	res = res.data;
	if (!res.data) {
		return;
	}
	let i = 0;
	let val = $("#edstats-indicator-name").val();
	let arr = res.data;
	for (i = 0; i < arr.length; i++) {
		let $newElem = $("<li>", {
			"class": "autocomplete-item list-group-item list-group-item-dark",
			"html": "<strong>" + arr[i].substr(0, val.length) + "</strong>" + arr[i].substr(val.length)
		});
		$newElem.on('click', function () {
			$("#edstats-indicator-name").val($(this).text());
		});
		$newElem.appendTo($('#autocomplete')[0]);
	}
}