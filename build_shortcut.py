import plistlib
import uuid
from pathlib import Path

UNSIGNED_SHORTCUT_PATH = Path(__file__).parent / "send-page-to-gwont.unsigned.shortcut"
VARIABLE_PLACEHOLDER = "\N{OBJECT REPLACEMENT CHARACTER}"

SCRAPE_PAGE_JAVASCRIPT = """
function scrapeTravianPage() {
	const playerName = document.querySelector("#sidebarBoxActiveVillage .content .playerName")?.textContent?.trim() ?? "";
	const uploadUrl =
		"https://api.gwont.com/export-page?url=" +
		encodeURIComponent(location.href) +
		"&avatar_name=" +
		encodeURIComponent(playerName);
	const plainBody = new Blob([document.documentElement.outerHTML]);

	function completeWithBody(body, contentEncoding) {
		const reader = new FileReader();
		reader.onload = () => completion({ uploadUrl, contentEncoding, bodyBase64: reader.result.split(",")[1] });
		reader.readAsDataURL(body);
	}

	if (typeof CompressionStream === "undefined") {
		completeWithBody(plainBody, "identity");
	} else {
		new Response(plainBody.stream().pipeThrough(new CompressionStream("gzip")))
			.blob()
			.then((gzippedBody) => completeWithBody(gzippedBody, "gzip"))
			.catch(() => completeWithBody(plainBody, "identity"));
	}
}

if (location.hostname.endsWith(".travian.com")) scrapeTravianPage();
else completion({ rejection: "not a Travian page" });
""".strip()

(
	api_key_id,
	scraped_page_id,
	rejection_id,
	rejection_check_id,
	upload_url_id,
	content_encoding_id,
	body_base64_id,
	body_id,
	response_id,
) = (str(uuid.uuid4()).upper() for _ in range(9))

api_key_action = {
	"WFWorkflowActionIdentifier": "is.workflow.actions.gettext",
	"WFWorkflowActionParameters": {"UUID": api_key_id, "WFTextActionText": ""},
}

scrape_page_action = {
	"WFWorkflowActionIdentifier": "is.workflow.actions.runjavascriptonwebpage",
	"WFWorkflowActionParameters": {
		"UUID": scraped_page_id,
		"WFJavaScript": SCRAPE_PAGE_JAVASCRIPT,
		"WFInput": {"Value": {"Type": "ExtensionInput"}, "WFSerializationType": "WFTextTokenAttachment"},
	},
}

scraped_page = {
	"Value": {"Type": "ActionOutput", "OutputUUID": scraped_page_id, "OutputName": "JavaScript Result"},
	"WFSerializationType": "WFTextTokenAttachment",
}

rejection_action = {
	"WFWorkflowActionIdentifier": "is.workflow.actions.getvalueforkey",
	"WFWorkflowActionParameters": {
		"UUID": rejection_id,
		"WFGetDictionaryValueType": "Value",
		"WFDictionaryKey": "rejection",
		"WFInput": scraped_page,
	},
}

HAS_ANY_VALUE = 100
IF, OTHERWISE, END_IF = 0, 1, 2

if_rejected_action = {
	"WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
	"WFWorkflowActionParameters": {
		"GroupingIdentifier": rejection_check_id,
		"WFControlFlowMode": IF,
		"WFCondition": HAS_ANY_VALUE,
		"WFInput": {
			"Type": "Variable",
			"Variable": {
				"Value": {"Type": "ActionOutput", "OutputUUID": rejection_id, "OutputName": "Dictionary Value"},
				"WFSerializationType": "WFTextTokenAttachment",
			},
		},
	},
}

not_travian_alert_action = {
	"WFWorkflowActionIdentifier": "is.workflow.actions.alert",
	"WFWorkflowActionParameters": {
		"WFAlertActionTitle": "Not a Travian page",
		"WFAlertActionMessage": "Nothing was sent to GWONT. Open a Travian page in Safari and try again.",
		"WFAlertActionCancelButtonShown": False,
	},
}

stop_action = {"WFWorkflowActionIdentifier": "is.workflow.actions.exit", "WFWorkflowActionParameters": {}}

otherwise_action = {
	"WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
	"WFWorkflowActionParameters": {"GroupingIdentifier": rejection_check_id, "WFControlFlowMode": OTHERWISE},
}

end_if_action = {
	"WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
	"WFWorkflowActionParameters": {"GroupingIdentifier": rejection_check_id, "WFControlFlowMode": END_IF},
}

upload_url_action = {
	"WFWorkflowActionIdentifier": "is.workflow.actions.getvalueforkey",
	"WFWorkflowActionParameters": {
		"UUID": upload_url_id,
		"WFGetDictionaryValueType": "Value",
		"WFDictionaryKey": "uploadUrl",
		"WFInput": scraped_page,
	},
}

content_encoding_action = {
	"WFWorkflowActionIdentifier": "is.workflow.actions.getvalueforkey",
	"WFWorkflowActionParameters": {
		"UUID": content_encoding_id,
		"WFGetDictionaryValueType": "Value",
		"WFDictionaryKey": "contentEncoding",
		"WFInput": scraped_page,
	},
}

body_base64_action = {
	"WFWorkflowActionIdentifier": "is.workflow.actions.getvalueforkey",
	"WFWorkflowActionParameters": {
		"UUID": body_base64_id,
		"WFGetDictionaryValueType": "Value",
		"WFDictionaryKey": "bodyBase64",
		"WFInput": scraped_page,
	},
}

decode_body_action = {
	"WFWorkflowActionIdentifier": "is.workflow.actions.base64encode",
	"WFWorkflowActionParameters": {
		"UUID": body_id,
		"WFEncodeMode": "Decode",
		"WFInput": {
			"Value": {"Type": "ActionOutput", "OutputUUID": body_base64_id, "OutputName": "Dictionary Value"},
			"WFSerializationType": "WFTextTokenAttachment",
		},
	},
}

upload_action = {
	"WFWorkflowActionIdentifier": "is.workflow.actions.downloadurl",
	"WFWorkflowActionParameters": {
		"UUID": response_id,
		"WFURL": {
			"Value": {
				"string": VARIABLE_PLACEHOLDER,
				"attachmentsByRange": {
					"{0, 1}": {"Type": "ActionOutput", "OutputUUID": upload_url_id, "OutputName": "Dictionary Value"}
				},
			},
			"WFSerializationType": "WFTextTokenString",
		},
		"WFHTTPMethod": "POST",
		"ShowHeaders": True,
		"WFHTTPHeaders": {
			"Value": {
				"WFDictionaryFieldValueItems": [
					{
						"WFItemType": 0,
						"WFKey": {"Value": {"string": "Authorization"}, "WFSerializationType": "WFTextTokenString"},
						"WFValue": {
							"Value": {
								"string": f"Bearer {VARIABLE_PLACEHOLDER}",
								"attachmentsByRange": {
									"{7, 1}": {"Type": "ActionOutput", "OutputUUID": api_key_id, "OutputName": "Text"}
								},
							},
							"WFSerializationType": "WFTextTokenString",
						},
					},
					{
						"WFItemType": 0,
						"WFKey": {"Value": {"string": "Content-Encoding"}, "WFSerializationType": "WFTextTokenString"},
						"WFValue": {
							"Value": {
								"string": VARIABLE_PLACEHOLDER,
								"attachmentsByRange": {
									"{0, 1}": {
										"Type": "ActionOutput",
										"OutputUUID": content_encoding_id,
										"OutputName": "Dictionary Value",
									}
								},
							},
							"WFSerializationType": "WFTextTokenString",
						},
					},
				]
			},
			"WFSerializationType": "WFDictionaryFieldValue",
		},
		"WFHTTPBodyType": "File",
		"WFRequestVariable": {
			"Value": {"Type": "ActionOutput", "OutputUUID": body_id, "OutputName": "Base64 Encoded"},
			"WFSerializationType": "WFTextTokenAttachment",
		},
	},
}

show_response_action = {
	"WFWorkflowActionIdentifier": "is.workflow.actions.notification",
	"WFWorkflowActionParameters": {
		"WFNotificationActionTitle": "GWONT",
		"WFNotificationActionSound": False,
		"WFNotificationActionBody": {
			"Value": {
				"string": VARIABLE_PLACEHOLDER,
				"attachmentsByRange": {
					"{0, 1}": {"Type": "ActionOutput", "OutputUUID": response_id, "OutputName": "Contents of URL"}
				},
			},
			"WFSerializationType": "WFTextTokenString",
		},
	},
}

actions = [
	api_key_action,
	scrape_page_action,
	rejection_action,
	if_rejected_action,
	not_travian_alert_action,
	stop_action,
	otherwise_action,
	end_if_action,
	upload_url_action,
	content_encoding_action,
	body_base64_action,
	decode_body_action,
	upload_action,
	show_response_action,
]

shortcut = {
	"WFWorkflowClientVersion": "2302.0.4",
	"WFWorkflowMinimumClientVersion": 900,
	"WFWorkflowMinimumClientVersionString": "900",
	"WFWorkflowIcon": {"WFWorkflowIconStartColor": 4282601983, "WFWorkflowIconGlyphNumber": 59511},
	"WFWorkflowTypes": ["ActionExtension"],
	"WFWorkflowInputContentItemClasses": ["WFSafariWebPageContentItem"],
	"WFWorkflowOutputContentItemClasses": [],
	"WFWorkflowHasShortcutInputVariables": True,
	"WFWorkflowImportQuestions": [
		{
			"ActionIndex": actions.index(api_key_action),
			"Category": "Parameter",
			"ParameterKey": "WFTextActionText",
			"DefaultValue": "",
			"Text": "Paste your GWONT API key. Create one on gwont.com under Settings, Account.",
		}
	],
	"WFWorkflowActions": actions,
}

UNSIGNED_SHORTCUT_PATH.write_bytes(plistlib.dumps(shortcut, fmt=plistlib.FMT_BINARY))
print(f"Wrote {UNSIGNED_SHORTCUT_PATH}")
