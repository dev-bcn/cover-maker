import axios from 'axios';
import * as fs from 'fs';

interface SessionizeSession {
    id: string;
    title: string;
    startsAt: string;
    speakers: {
        name: string;
    }[];
    categories: {
        name: string;
        categoryItems: {
            name: string;
        }[];
    }[];
}

interface Talk {
    title: string;
    speakers: string;
    track: string;
    start_time: string;
}

async function fetchSessions(): Promise<Talk[]> {
    try {
        const response = await axios.get('https://sessionize.com/api/v2/xhudniix/view/Sessions');
        const data = response.data;
        
        const talks: Talk[] = [];
        
        // Process each group's sessions
        data.forEach((group: any) => {
            group.sessions.forEach((session: SessionizeSession) => {
                // Get the track from categories
                const trackCategory = session.categories.find(cat => cat.name === "Track");
                const track = trackCategory?.categoryItems[0]?.name.toLowerCase() || "main";
                
                // Format speakers names
                const speakerNames = session.speakers.map(s => s.name).join(" & ");
                
                // Format start time
                const startTime = new Date(session.startsAt);
                const formattedTime = `${startTime.getHours().toString().padStart(2, '0')}:${startTime.getMinutes().toString().padStart(2, '0')}`;
                
                talks.push({
                    title: session.title,
                    speakers: speakerNames,
                    track: track === "java & jvm (core frameworks & libraries, kotlin, scala, groovy, architecture)" ? "java" : track,
                    start_time: formattedTime
                });
            });
        });
        
        return talks;
    } catch (error) {
        console.error('Error fetching sessions:', error);
        throw error;
    }
}

async function generateSpeakersFile() {
    try {
        const talks = await fetchSessions();
        
        // Create the file content
        const fileContent = `var talks = ${JSON.stringify(talks, null, 2)};\n\n` +
            `// Open the image file\n` +
            `var doc = app.open(File("~/Documents/DevBcn/devbcn-rotulo-2025.psd"));\n\n` +
            `// Iterate through the talks array\n` +
            `for (var i = 0; i < talks.length; i++) {\n` +
            `    var talk = talks[i];\n\n` +
            `    // Get the title and speakers from the talk object\n` +
            `    var title = talk.title;\n` +
            `    var speakers = talk.speakers;\n` +
            `    var track = talk.track;\n` +
            `    var start_time = talk.start_time;\n\n` +
            `    var talkLayer = doc.artLayers.getByName("talk");\n` +
            `    talkLayer.textItem.contents = title;\n` +
            `    var speakerLayer = doc.artLayers.getByName("speakers");\n` +
            `    speakerLayer.textItem.contents = speakers;\n\n` +
            `    // Save a copy of the modified image with a unique name\n` +
            `    var saveFile = new File("~/Documents/DevBcn/rotulos/2025/" + track + "/" + start_time.replace(":", "-") + "_" + speakers.replace(/(?:\\s+|" y "|" & " )/g, "-") + ".png");\n` +
            `    var saveOptions = new ExportOptionsSaveForWeb();\n` +
            `    saveOptions.format = SaveDocumentType.PNG;\n` +
            `    saveOptions.PNG8 = false; // Use true if you want 8-bit PNG\n` +
            `    doc.exportDocument(saveFile, ExportType.SAVEFORWEB, saveOptions);\n` +
            `}\n\n` +
            `// Close the document\n` +
            `doc.close();\n`;
        
        // Write to file
        fs.writeFileSync('devbcn-speakers-2025.js', fileContent);
        console.log('Successfully generated devbcn-speakers-2025.js');
        
    } catch (error) {
        console.error('Error generating speakers file:', error);
    }
}

generateSpeakersFile(); 