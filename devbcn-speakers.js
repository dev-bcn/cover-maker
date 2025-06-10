var talks = [
    //People track
    {
        title: "Learning from Failures: Ways to Improve Chances of Success",
        speakers: "Venkat Subramaniam",
        track: "people",
        start_time:"9:10"
    }, {
        title: "Aprendiendo a gestionar... por las bravas",
        speakers: "Pablo Bouzada Santomé",
        track: "people",
        start_time:"11:10"
    }, {
        title: "Battling your Biased Brain",
        speakers: "Peter Wessels",
        track: "people",
        start_time:"12:15"
    }, {
        title: "Three cups of Java",
        speakers: "Vincent Mayers",
        track: "people",
        start_time:"14:30"
    }, {
        title: "Creating Psychologically Safe Engineering Teams",
        speakers: "Jessie Auguste",
        track: "people",
        start_time:"15:35"
    }, {
        title: "No busques más, la solución esta en el feedback",
        speakers: "Josep Ma Rocamora Batalla y Elena Navarro Molina",
        track: "people",
        start_time:"17:05"
    }, {
        title: "What I learnt running in the artic: Lessons for leadership in engineering",
        speakers: "Marta Padilla Montoliu",
        track: "people",
        start_time:"18:10"
    }, {
        title: "De la estrategia a la ejecución. ¿Qué significa realmente ser ágil?",
        speakers: "Alberto Tordesillas",
        track: "people",
        start_time:"9:00"
    }, {
        title: "Developer Productivity Engineering: What's in it for me?",
        speakers: "Trisha Gee",
        track: "people",
        start_time:"10:00"
    }, {
        title: "How to Become a Top-Performing Software Engineer through Real-World Open Source Practices",
        speakers: "Karina Varela",
        track: "people",
        start_time:"11:15"
    }, {
        title: "Como implementar un cambio desde abajo con Digital Leaders",
        speakers: "Ruben Barcia",
        track: "people",
        start_time:"12:20"
    }, {
        title: "Tech Sherpas: 5 Keys for Effective Leadership",
        speakers: "Alvaro Moya",
        track: "people",
        start_time:"14:30"
    }, {
        title: "Sustainable code",
        speakers: "Carlos Blé Jurado y Maria Soria Dura",
        track: "people",
        start_time:"15:25"
    }, {
        title: "P3.express, the power of routine",
        speakers: "Elisabet Duocastella Pla",
        track: "people",
        start_time:"17:00"
    }, {
        title: "Improve team building on full-remote teams",
        speakers: "Marina Planells Guasch",
        track: "people",
        start_time:"17:25"
    }, {
        title: "De Design Thinking a Circular Design Thinking",
        speakers: "Luciano Wehrli",
        track: "people",
        start_time:"09:00"
    }, {
        title: "Sueños, quejas y agilidad: sacando a Calimero a pasear",
        speakers: "María Mira Herreros",
        track: "people",
        start_time:"11:40"
    },
//Java
    {
        title: "About Giants, Liars and Slow Pokes...A (Unit-) Test-Antipattern-Fairytale",
        speakers: "Birgit Kratz",
        track: "java",
        start_time:"11:10"
    },
    {
        title: "Building modular libraries for 120 teams: our findings",
        speakers: "Fabio Pezzoni & MAksym Telepchuk",
        track: "java",
        start_time:"12:15"
    },{
        title: "A Healthy diet for your Java application",
        speakers: "Marharyta Nedzelska Nedzelska",
        track: "java",
        start_time:"14:30"
    }, {
        title: "Deserialization exploits in Java: why should I care?",
        speakers: "BRIAN VERMEER",
        track: "java",
        start_time:"15:35"
    },
    {
        title: "Stork: descubre servicios fácilmente y selecciona el mejor",
        speakers: "Aurea Muñoz Hernandez",
        track: "java",
        start_time:"17:05"
    },{
        title: "JBang and the prisoner of the release",
        speakers: "Jordi Sola",
        track: "java",
        start_time:"17:30"
    },{
        title: "Reactive Java",
        speakers: "Joaquin Azcarate",
        track: "java",
        start_time:"18:10"
    },{
        title:"Welcome Keynote",
        speakers:"Nacho Cougil & Jonathan Vila",
        track:"Java",
        start_time:"8:40"
    },
    {
        title:"Closing Keynote",
        speakers:"Nacho Cougil & Jonathan Vila",
        track:"Java",
        start_time:"18:45"
    },
    {
        title: "How to avoid common pitfalls with modern microservices testing",
        speakers: "Eric Deandrea & Holly Cummins",
        track: "java",
        start_time:"9:00"
    },{
        title:"To the moon, via the cloud!",
        speakers:"David Creer",
        track:"java",
        start_time:"9:55"
    },{
        title: "Jakarta EE! The future of enterprise application behind the myths.",
        speakers: "Alberto Salazar",
        track: "java",
        start_time:"10:00"
    },{
        title: "Jakarta EE: Success comes with strong open source community",
        speakers: "Shabnam Mayel",
        track: "java",
        start_time:"11:15"
    },{
        title: "Maven Central++ What's happening at the core of the Java supply chain",
        speakers: "Steve Poole",
        track: "java",
        start_time:"12:20"
    },{
        title: "Say goodbye to bugs and anti-patterns with Error Prone",
        speakers: "Rick Ossendrijver",
        track: "java",
        start_time:"14:30"
    },{
        title: "Serverless Java with Spring Boot",
        speakers: "Thomas Vitale",
        track: "java",
        start_time:"15:25"
    },{
        title: "Welcome to the Jungle - A safari through the JVM landscape",
        speakers: "Gerrit Grunwald",
        track: "java",
        start_time:"17:00"
    },{
        title: "Parenting + Sports = Tech Teams Management",
        speakers: "Carlos Buenosvinos",
        track: "java",
        start_time:"18:00"
    }
];

// Open the image file
var doc = app.open(File("~/Documents/DevBcn/devbcn-rotulo.psd"));

// Iterate through the talks array
for (var i = 0; i < talks.length; i++) {
    var talk = talks[i];

    // Get the title and speakers from the talk object
    var title = talk.title;
    var speakers = talk.speakers;
    var track = talk.track;
    var start_time = talk.start_time;

    var talkLayer = doc.artLayers.getByName("talk");
    talkLayer.textItem.contents = title;
    var speakerLayer = doc.artLayers.getByName("speakers");
    speakerLayer.textItem.contents = speakers;

    // Save a copy of the modified image with a unique name
    //java-10-00_Venkat-subramaniam.png
    var saveFile = new File("~/Documents/DevBcn/rotulos/"+track+"-"+start_time.replace(":","-") +"_"+ speakers.replace(/(?:\s+|" y "|" & " )/g, "-") + ".png");
    var saveOptions = new ExportOptionsSaveForWeb();
    saveOptions.format = SaveDocumentType.PNG;
    saveOptions.PNG8 = false; // Use true if you want 8-bit PNG
    doc.exportDocument(saveFile, ExportType.SAVEFORWEB, saveOptions);
}

// Close the document
doc.close();
