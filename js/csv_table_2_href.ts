interface NodeListOf<TNode extends Node> extends Array<TNode>
{
}

interface HTMLCollectionBase extends Array<Element>
{
}

document.addEventListener(
	"DOMContentLoaded",
	(dom_event) =>
	{
		const base64encode = (string: string) =>
			btoa(
				encodeURIComponent(string)
					.replace(
						/%([0-9A-F]{2})/g,
						(match, p1) =>
							String.fromCharCode(
								parseInt(
									p1,
									16,
								),
							),
					),
			);
		const table2data = (table_element: HTMLTableElement) =>
		{
			const data: string[][] = [];
			for(const tr of table_element.getElementsByTagName("tr"))
			{
				const data_row: string[] = [];
				for(const element of (<HTMLTableRowElement>tr).children)
				{
					const inputs = (<HTMLInputElement[]> element.getElementsByTagName("input"));
					if(inputs.length > 0)
					{
						const input = inputs[0];
						if(input.type === "checkbox")
						{
							if(input.checked)
							{
								data_row.push("1");
								continue;
							}
							data_row.push("");
							continue;
						}
						data_row.push(input.value);
						continue;
					}
					//data_row.push(element.innerText);
					data_row.push((<HTMLElement> element).innerText);
				}
				data.push(data_row);
			}
			return data;
		};
		const data2csv = (data: string[][], separator: string, surround: string = "\"", escape: string = "\"\"") =>
			(surround && surround.length > 0) ?
				data.map(
					(row) => row.map(
						(cell) => surround + ("" + cell).replace(new RegExp(surround, "g"), escape) + surround,
					)
						.join(separator),
				)
					.join("\n")
				:
				data.map(
					(row) => row.join(separator),
				)
					.join("\n");
		const csv2href = (csv_data: string, mime_type: string = "text/csv") => "data:" + mime_type + ";base64," + base64encode(csv_data);

		const csv_link: HTMLAnchorElement = (<HTMLAnchorElement> document.getElementById("csv_export"));
		csv_link.addEventListener(
			"click",
			(click_event) =>
				csv_link.href = csv2href(data2csv(table2data((<HTMLTableElement>document.getElementById("maintable"))), ";")),
		)
		;
	},
)
;
