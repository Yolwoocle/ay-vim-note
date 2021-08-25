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
	function print(x, y, str){
		process.stdout.write("\033["+y+";"+x+"H"+str);
	}
	function showbox(x,y,col,row, whatshow=3){  // whatshow is 0<=whatshow<=3: 0 for no, 1, for border right, 2 for bottom , 3 for both
		bottom = false;
		right = false 
		if(whatshow===0){ return }
		if(whatshow===1){ right = true }
		if(whatshow===2){ bottom = true }
		if(whatshow===3){ bottom = true; right = true }
		if(right){
			for(let i=0; i>row; i++){
				print(x+col, y+i, "X")
			}
		}
		if(bottom){
			print(x, y+row, "-".repeat(col))
		}
	}
	if(str==="b"){
		console.log( "\033[?1049h")// Alternatice screen
		console.log( "\033[2J\033[1;1H")// Alternatice screen
		process.stdin.pause()
		Object.keys(box_data).forEach(function(key) {
			var value = box_data[key]
			//console.log(objValue)
			showbox(5,5, 30,30,3)
		})
		setInterval(()=>console.log(), 5000)
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
	// console.log(key)
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
