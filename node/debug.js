const watch = require('node-watch')
var fs = require('fs');
  
function read_file(){
	console.log("\033[2J\033[1;1H")
	fs.readFile('debug.md', 'utf8', function(err, data){
		try{
			console.log(JSON.parse(data));
		} catch {
			console.log(data);
		}
	});
}

watch('debug.md', function(event, filename) {
	read_file()
})

