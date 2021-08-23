#!/usr/bin/env node
const readline = require('readline');
const fs = require('fs');
const path = require('path');

nerd_font = true 

let matiere_data = {}
let config = {
	"editor": "vim", // need to be launchabe with terminal
	"nerd_font": nerd_font,
	"icons": {
		"folder_close": nerd_font ? "\uf07b" : ">",
		"folder_open": nerd_font? "\uf07c" : "v",
		"no_file": nerd_font ? "\ue612" : "-",
	},
	// if nerd_font is off we set all icons to -
	"ext_icons": nerd_font ? {
		"unknown": "\ue612",
		"md": "\uf48a",
		"image": "\uf03e",
	}:{ "unknown" : "-" },
	"path": "/home/ay/Cours2022Git/notes",
}
let infos = {
	"vim_is_open": false,
	"col": process.stdout.columns,
	"row": process.stdout.rows,
	"boxs": {
		"M": {
			"name": "Matière",
			"": ""
		}
	},
}
let box_data = {
	"x": 1,
	"y": 1,
	"col": infos.col,
	"row": infos.row,
	"vertical": true, // si la page est vertical ou non 
	"boxs":{
		"0": {
			"x": 0,
			"y": 0,
			"col": 70,
			"row": 20,
		},
		"1": {
			"x": 70,
			"y": 20,
			"col": infos.col,
			"row": infos.row,
		},
		"2": {
			"3": {
				
			}
		}
	}
	
}
let folder_data = {}

let new_box = {}

function generate_folder_data(){
	fs.readdir(config.path, { withFileTypes: true },(err, matieres) => {
		// Pour toutes les matières
		matieres.forEach(matiere => {
			if(matiere.isDirectory()){
				matiere_path = path.join(config.path, matiere.name)
				// Pour toutes les parties
				parties = fs.readdirSync(matiere_path, { withFileTypes: true })
				parties.forEach(partie => {
					if(partie.isDirectory()){
						matiere_data[partie.name] = {
							"path": path.join(matiere_path, partie.name),
							"fold": true,
							"name": partie.name,
							"type": "Folder",
							"numero": 0,
							"long": 0,
							"files": {}
						} 
						cours = fs.readdirSync(matiere_data[partie.name].path, { withFileTypes: true })
						cours.forEach(cour => {
							ext = cour.name.match("\\.([a-z]+)") === null ? undefined : cour.name.match("\\.([a-z]+)")[1]
							if(config.ext_icons.hasOwnProperty(ext)){
								ext_logo = config.ext_icons[ext]
							}else{
								ext_logo = config.ext_icons["unknown"]
							} 
							matiere_data[partie.name].files[cour.name] = {
								"name": cour.name,
								"path": path.join(matiere_data[partie.name].path, cour.name),
								"ext": ext,
								"ext_logo": ext_logo,
							}
							
						})
						console.log(matiere_data[partie.name])
					}
				})
			}
		})
	})
}

function launch_editor(file){
	var vim = require('child_process').spawn(config.editor ,[file], {stdio: 'inherit'});
	vim.on('exit', () => { process.stdin.resume() })
}

function clear(){ console.log("\033[2J\033[1;1H") }
function exit(){ console.log( "\033[?25h"+ "\033[?1049l"); process.exit();  }//show cursor 
function main(str, key){
	if(str==="8"){
		fs.writeFileSync('/home/ay/ay-vim-note/node/debug.md', JSON.stringify([infos, config, infos.boxs]));
	}
	if(str==="d"){
		console.log(matiere_data)
	}
	if(str==="a"){
		console.table(config)
		console.table(infos)
		console.table(box_data)
	}
	// STOP AND DROW Box
	if(str==="b"){
		console.log( "\033[?1049h")// Alternatice screen
		process.stdin.pause()
		var objectKeysArray = Object.keys(box_data)
		objectKeysArray.forEach(function(objKey) {
			var objValue = box_data[objKey]
			console.log(objValue)
		})

		// box_data.forEach(name =>{console.log(name)})
	}
	if(str==="0"){generate_folder_data()}
	// if(str==="0"){new_box()}
	if(str === "\x03"){ exit() }
	if(str === "\x04"){
		process.stdin.pause()
		launch_editor("test.txt")
	}
	console.log(str)
	console.log(key)
}

process.on('SIGWINCH', () => {
	infos.columns = process.stdout.columns;
	infos.rows = process.stdout.rows;
});
readline.emitKeypressEvents(process.stdin);
process.stdin.setRawMode(true);
// console.log( "\033[?1049h")// Alternatice screen
console.log( "\033[?1002h\033[?1015h\033[?1006h") // Mouse on
// console.log( "\033[?25l") //Hide cursor 
process.stdin.on('keypress', (str, key) => main(str, key))

// DEBUG
/*
debug = true
function reload() {
    setTimeout(() => reload(), 1000);
    if (debug) {
		fs.writeFileSync('/home/ay/ay-vim-note/node/debug.md', JSON.stringify(infos));
    }
}
reload()
*/
