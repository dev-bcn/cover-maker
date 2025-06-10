var talks =
    [{
        title: "Welcome Keynote",
        speakers: "Nacho Cougil & Jonathan Vila",
        track: "main",
        start_time: "8:40"
    }, {
        title: "Accelerating GenAI Development for LLM-Powered Apps",
        speakers: "David Laconte",
        track: "main",
        start_time: "9:10"
    }, {
        title: "Time To Take Action on Climate Change & Sustainability",
        speakers: "Max Schulze",
        track: "main",
        start_time: "9:55"
    },
        {
            title: "Closing Keynote",
            speakers: "Nacho Cougil & Jonathan Vila",
            track: "main",
            start_time: "18:45"
        },
        {
            title: "Developing a full stack reactive application using Kubernetes as event producer",
            speakers: "Marc Nuri",
            track: "main",
            start_time: "11:10:00"
        }, {
        title: "Unleashing the Power of Serverless on Kubernetes with Knative, Crossplane, Dapr & KEDA",
        speakers: "Mauricio 'Salaboy' Salatino",
        track: "kcd",
        start_time: "11:10:00"
    }, {
        title: "Enhancing Productivity and Insight: A Tour of JDK Tools Progress Beyond Java 17",
        speakers: "Ana Maria Mihalceanu",
        track: "main",
        start_time: "12:15:00"
    }, {
        title: "No passwords, no problem: move beyond passwords with webauthn and passkeys",
        speakers: "Carla Urrea Stabile",
        track: "kcd",
        start_time: "12:15:00"
    }, {
        title: "From Spring Boot 2 to Spring Boot 3 with Java 21 and Jakarta EE",
        speakers: "Ivar Grimstad",
        track: "main",
        start_time: "14:10:00"
    }, {
        title: "From Silos to DevOps to Platform Engineering: embracing GitOps and going behind the hype",
        speakers: "Horacio Gonzalez",
        track: "kcd",
        start_time: "14:10:00"
    }, {
        title: "Setting up data driven tests with Java tools",
        speakers: "Andres Almiray",
        track: "main",
        start_time: "15:15:00"
    }, {
        title: "From FTP to ArgoCD & Argo Rollouts: An adoption history inside a corp",
        speakers: "Jorge Turrado & Alfonso Ming",
        track: "kcd",
        start_time: "15:15:00"
    }, {
        title: "Code coverage MythBusters",
        speakers: "Marharyta Nedzelska & Evgeny Mandrikov",
        track: "main",
        start_time: "16:40:00"
    }, {
        title: "DevOps and Baking",
        speakers: "Heather Thacker",
        track: "kcd",
        start_time: "16:40:00"
    }, {
        title: "Cloud Native apps with Micronaut 4 and GraalVM",
        speakers: "Graeme Rocher",
        track: "main",
        start_time: "18:00:00"
    }, {
        title: "Kubernetes-Driven Multi-Cloud Deployments: Maximizing Scalability and Flexibility",
        speakers: "Lori King",
        track: "kcd",
        start_time: "18:00:00"
    }, {
        title: "Are Your Tests Slowing You Down?",
        speakers: "Trisha Gee",
        track: "main",
        start_time: "09:00:00"
    }, {
        title: "Telemetry Showdown: Fluent Bit vs. OpenTelemetry Collector - A Comprehensive Benchmark Analysis",
        speakers: "Henrik Rexed",
        track: "kcd",
        start_time: "09:00:00"
    }, {
        title: "GC Algorithms for the Cloud",
        speakers: "Pratik Patel",
        track: "main",
        start_time: "10:05:00"
    }, {
        title: "Shield your backend from outside attacks with API Managers",
        speakers: "Barbara Teruggi",
        track: "kcd",
        start_time: "10:05:00"
    }, {
        title: "ML in Java, YES it's possible!",
        speakers: "Mohammed Aboullaite",
        track: "main",
        start_time: "11:20:00"
    }, {
        title: "Navigating and Optimizing Karpenter - Avoiding Common Pitfalls",
        speakers: "Ivan Yurochko",
        track: "kcd",
        start_time: "11:20:00"
    }, {
        title: "The chaos incarnated: Micro-Quarkus Boot!",
        speakers: "Maria Arias de Reyna Dominguez",
        track: "main",
        start_time: "12:25:00"
    }, {
        title: "Operación Crossplane: Tácticas de comando en la nube",
        speakers: "Joan Miquel Luque Oliver",
        track: "kcd",
        start_time: "12:25:00"
    }, {
        title: "Too heavy for the Chevy? JLink to the rescue",
        speakers: "Gerrit Grunwald",
        track: "main",
        start_time: "14:30:00"
    }, {
        title: "Building GDPR, ISO27001 Containerized Application for continuous compliance",
        speakers: "Dhiraj Sehgal",
        track: "kcd",
        start_time: "14:30:00"
    }, {
        title: "Building Sustainable Software with Java: Tips & Techniques",
        speakers: "Aicha Laafia",
        track: "main",
        start_time: "15:00:00"
    }, {
        title: "Solving Challenges of use Reactive and Non-Reactive Services in the Real World !",
        speakers: "Alberto Salazar",
        track: "main",
        start_time: "15:45:00"
    }, {
        title: "Dapr in Practice",
        speakers: "Marc Klefter",
        track: "kcd",
        start_time: "15:45:00"
    }, {
        title: "Observability In Java By Example",
        speakers: "Ben Evans",
        track: "main",
        start_time: "17:00:00"
    }, {
        title: "Practical guides for enhaching your Software Supply Chain Security",
        speakers: "Abdel Sghiouar",
        track: "kcd",
        start_time: "17:00:00"
    }
        , {
        title: "Boost Performance and Developer Productivity with Jakarta EE 11",
        speakers: "Ivar Grimstad",
        track: "main",
        start_time: "18:00:00"
    }
        , {
        title: "AI will rule the world - can we rule AI?",
        speakers: "Jens Grivolla",
        track: "main",
        start_time: "18:00:00"
    },
        {
            title: "Trash Talk - Exploring the memory management in the JVM",
            speakers: "Gerrit Grunwald",
            track: "main",
            start_time: "17:00:00"

        }

    ]
;

// Open the image file
var doc = app.open(File("~/Documents/DevBcn/devbcn-rotulo-2024.psd"));

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
    var saveFile = new File("~/Documents/DevBcn/rotulos/2024/" + track + "/" + start_time.replace(":", "-") + "_" + speakers.replace(/(?:\s+|" y "|" & " )/g, "-") + ".png");
    var saveOptions = new ExportOptionsSaveForWeb();
    saveOptions.format = SaveDocumentType.PNG;
    saveOptions.PNG8 = false; // Use true if you want 8-bit PNG
    doc.exportDocument(saveFile, ExportType.SAVEFORWEB, saveOptions);
}

// Close the document
doc.close();
