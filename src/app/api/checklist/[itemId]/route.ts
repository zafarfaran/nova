import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { db } from "~/server/db";

const UpdateSchema = z.object({
    status: z.string().optional(),
    uploadedFileUrl: z.string().optional(),
});

export async function PATCH(
    request: NextRequest,
    { params }: { params: Promise<{ itemId: string }> }
) {
    try {
        const { itemId } = await params;
        const itemIdNum = parseInt(itemId, 10);

        if (isNaN(itemIdNum)) {
            return NextResponse.json(
                { success: false, message: "Invalid item ID" },
                { status: 400 }
            );
        }

        const body = await request.json();
        const validatedData = UpdateSchema.parse(body);

        // Update the checklist item
        const updatedItem = await db.checklistItem.update({
            where: { id: itemIdNum },
            data: validatedData,
        });

        return NextResponse.json({
            success: true,
            data: updatedItem,
        });
    } catch (error) {
        if (error instanceof z.ZodError) {
            return NextResponse.json(
                {
                    success: false,
                    message: "Invalid payload",
                    errors: error.errors,
                },
                { status: 400 }
            );
        }

        console.error("Error updating checklist item:", error);
        return NextResponse.json(
            {
                success: false,
                message: "Internal server error",
            },
            { status: 500 }
        );
    }
}
