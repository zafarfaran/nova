import { createUploadthing, type FileRouter } from "uploadthing/next";
import { UploadThingError } from "uploadthing/server";
import { db } from "~/server/db";
import { z } from "zod";

const f = createUploadthing();

// FileRouter for client onboarding documents
export const ourFileRouter = {
    // Document uploader for checklist items
    documentUploader: f({
        pdf: { maxFileSize: "10MB", maxFileCount: 5 },
        image: { maxFileSize: "10MB", maxFileCount: 5 },
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {
            maxFileSize: "10MB",
            maxFileCount: 5,
        },
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
            maxFileSize: "10MB",
            maxFileCount: 5,
        },
        "text/csv": { maxFileSize: "10MB", maxFileCount: 5 },
    })
        .input(
            z.object({
                clientId: z.string(),
                checklistItemId: z.string(),
            })
        )
        .middleware(async ({ input }) => {
            const { clientId, checklistItemId } = input;

            // Verify the checklist item exists
            const checklistItem = await db.checklistItem.findUnique({
                where: { id: checklistItemId },
                include: { clientSetup: true },
            });

            if (!checklistItem || checklistItem.clientSetupId !== clientId) {
                throw new UploadThingError("Invalid checklist item");
            }

            return {
                clientId,
                checklistItemId,
                itemTitle: checklistItem.title,
            };
        })
        .onUploadComplete(async ({ metadata, file }) => {
            console.log("Upload complete for checklist item:", metadata.checklistItemId);
            console.log("File URL:", file.url);

            // Update the checklist item with the uploaded file URL and status
            await db.checklistItem.update({
                where: { id: metadata.checklistItemId },
                data: {
                    uploadedFileUrl: file.url,
                    status: "uploaded",
                },
            });

            return {
                uploadedBy: metadata.clientId,
                fileUrl: file.url,
                itemTitle: metadata.itemTitle,
            };
        }),
} satisfies FileRouter;

export type OurFileRouter = typeof ourFileRouter;
