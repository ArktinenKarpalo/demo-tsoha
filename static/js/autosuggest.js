tags = []; // Tags to search matches from, sorted so we can find a range of strings that match the given prefix
beginIndex = 0; // First index in tags which matches
curIndex = 0; // Index currently selected by user
endIndex = 0; // Last index in tags which matches
tag_li = []; // Elements of autosuggestion list presented to the user

init = (input_field) => {
	suggestion_list = null;

	input_field.addEventListener("focusout", (ev) => {
		if(suggestion_list != null && suggestion_list.parentNode != null)
			input_field.parentNode.removeChild(suggestion_list);
	});
	document.addEventListener("keydown", (ev) => {
		if(ev.key == "Enter") {
			ev.preventDefault();
			return false;
		}
	});
	input_field.addEventListener("keydown", (ev) => {
		if(ev.key == "ArrowUp")
			setIndex(curIndex-1);
		else if(ev.key == "ArrowDown")
			setIndex(curIndex+1);
		else if(ev.key == "Enter") {
			if(suggestion_list != null && suggestion_list.parentNode != null && curIndex >= beginIndex && curIndex < endIndex) {
				input_tags = input_field.value;
				input_tags = input_tags.split(" ");
				input_tags[input_tags.length-1] = tag_li[curIndex-beginIndex].textContent;
				input_tags = input_tags.join(" ");
				input_field.value = input_tags + " ";
				beginIndex = -1;
				input_field.parentNode.removeChild(suggestion_list);
				ev.preventDefault();
				return false;
			} else {
				if(input_field.type == "search")
					search(input_field);
				else
					input_field.parentNode.parentNode.submit();
				return true;
			}
		} else {
			return true;
		}
		ev.preventDefault();
		return false;
	});
	input_field.addEventListener("input", (ev) => {
		input_tags = input_field.value.split(" ");
		suggestTags(input_tags[input_tags.length-1])
		endIndex = Math.min(endIndex, beginIndex+10)
		if(suggestion_list != null && suggestion_list.parentNode != null)
			input_field.parentNode.removeChild(suggestion_list);
		tag_li = []
		suggestion_list = document.createElement("ul");
		suggestion_list.style = "position: absolute; background-color: rgba(44, 62, 80, 1.0); transform: translate(10px, 0); margin: 0;";
		for(let i=beginIndex; i<endIndex; i++) {
			const li = document.createElement("li");
			li.textContent = tags[i];
			suggestion_list.appendChild(li);
			tag_li.push(li);
		}
		input_field.parentNode.appendChild(suggestion_list);
		setIndex(beginIndex);
	});
}

setIndex = (index) => {
	if(curIndex >= beginIndex && curIndex < endIndex) {
		tag_li[curIndex-beginIndex].style = "background-color: none;"
	}
	if(index >= endIndex)
		index = beginIndex;
	else if(index < beginIndex)
		index = endIndex-1;
	curIndex = index;
	if(curIndex >= beginIndex && curIndex < endIndex) {
		tag_li[curIndex-beginIndex].style = "background-color: black;";
		tag_li[curIndex-beginIndex].style = "background-color: black;";
	}
};

suggestTags = (search) => {
	if(search.length == 0) {
		endIndex = -1;
		return;
	}
	beginIndex = -1;
	for(let i = Math.log(tags.length)/Math.log(2); i>=0; i--) {
		suggestion = beginIndex+(1<<i);
		if(suggestion >= tags.length)
			continue;
		if(search > tags[suggestion]) {
			beginIndex = suggestion;
		}
	}
	endIndex = tags.length;
	for(let i = Math.log(tags.length)/Math.log(2); i>=0; i--) {
		suggestion = endIndex-(1<<i);
		if(suggestion < 0)
			continue;
		if(search < tags[suggestion] && !tags[suggestion].startsWith(search)) {
			endIndex = suggestion;
		}
	}
	beginIndex++;
};

const req = new XMLHttpRequest();
req.addEventListener("load", () => {
	if(req.status == 200) {
		tags = JSON.parse(req.response).map((ar)=>ar[0]);
		tags = tags.sort((a,b) => {
			if(a == b)
				return 0;
			else if(a > b)
				return 1;
			else
				return -1;
		});
	}
});

req.open("GET", "/tags");
req.send();
